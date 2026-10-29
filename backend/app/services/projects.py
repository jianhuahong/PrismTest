from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import roles
from app.models.project import Project, ProjectMember
from app.models.user import User


class DuplicateProjectKey(Exception):
    pass


class ProjectNotFound(Exception):
    pass


class ProjectDenied(Exception):
    pass


class UserNotFound(Exception):
    pass


class AlreadyMember(Exception):
    pass


class InvalidMemberRole(Exception):
    pass


@dataclass
class ProjectContext:
    project: Project
    my_role: str
    can_write: bool


def _context(project: Project, my_role: str, can_write: bool) -> ProjectContext:
    return ProjectContext(project=project, my_role=my_role, can_write=can_write)


async def get_access(session: AsyncSession, user: User, project_id: int) -> ProjectContext:
    project = await session.get(Project, project_id)
    if user.role == roles.PLATFORM_ADMIN:
        if project is None:
            raise ProjectNotFound
        return _context(project, roles.PLATFORM_ADMIN, True)
    if project is None:
        raise ProjectDenied
    member = await session.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.id,
        )
    )
    if member is None:
        raise ProjectDenied
    return _context(project, member.role, member.role in roles.PROJECT_WRITERS)


async def create_project(session: AsyncSession, user: User, name: str, key: str) -> ProjectContext:
    existing = await session.scalar(select(Project).where(Project.key == key))
    if existing is not None:
        raise DuplicateProjectKey
    project = Project(name=name, key=key, owner_id=user.id)
    session.add(project)
    await session.flush()
    session.add(
        ProjectMember(project_id=project.id, user_id=user.id, role=roles.PROJECT_OWNER)
    )
    await session.commit()
    await session.refresh(project)
    my_role = roles.PLATFORM_ADMIN if user.role == roles.PLATFORM_ADMIN else roles.PROJECT_OWNER
    return _context(project, my_role, True)


async def list_projects(session: AsyncSession, user: User) -> list[ProjectContext]:
    if user.role == roles.PLATFORM_ADMIN:
        projects = (await session.scalars(select(Project).order_by(Project.id))).all()
        return [_context(project, roles.PLATFORM_ADMIN, True) for project in projects]

    rows = (
        await session.execute(
            select(Project, ProjectMember.role)
            .join(ProjectMember, ProjectMember.project_id == Project.id)
            .where(ProjectMember.user_id == user.id)
            .order_by(Project.id)
        )
    ).all()
    return [
        _context(project, role, role in roles.PROJECT_WRITERS) for project, role in rows
    ]


async def rename_project(session: AsyncSession, project: Project, name: str) -> Project:
    project.name = name
    await session.commit()
    await session.refresh(project)
    return project


async def add_member(
    session: AsyncSession,
    ctx: ProjectContext,
    username: str,
    role: str,
) -> ProjectMember:
    if ctx.my_role not in (roles.PLATFORM_ADMIN, roles.PROJECT_OWNER):
        raise ProjectDenied
    if role not in roles.PROJECT_ROLES:
        raise InvalidMemberRole
    target = await session.scalar(select(User).where(User.username == username))
    if target is None:
        raise UserNotFound
    existing = await session.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == ctx.project.id,
            ProjectMember.user_id == target.id,
        )
    )
    if existing is not None:
        raise AlreadyMember
    member = ProjectMember(project_id=ctx.project.id, user_id=target.id, role=role)
    session.add(member)
    await session.commit()
    await session.refresh(member)
    return member


async def list_members(session: AsyncSession, project_id: int) -> list[tuple[ProjectMember, str]]:
    rows = (
        await session.execute(
            select(ProjectMember, User.username)
            .join(User, User.id == ProjectMember.user_id)
            .where(ProjectMember.project_id == project_id)
            .order_by(ProjectMember.id)
        )
    ).all()
    return [(member, username) for member, username in rows]
