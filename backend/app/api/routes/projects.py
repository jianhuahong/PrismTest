from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import project_access, require_role
from app.core import roles
from app.core.database import get_db
from app.models.user import User
from app.schemas.project import MemberCreate, MemberOut, ProjectCreate, ProjectOut, ProjectUpdate
from app.services import projects as project_service
from app.services.projects import (
    AlreadyMember,
    DuplicateProjectKey,
    InvalidMemberRole,
    ProjectContext,
    ProjectDenied,
    UserNotFound,
)

router = APIRouter()


def _out(ctx: ProjectContext) -> ProjectOut:
    project = ctx.project
    return ProjectOut(
        id=project.id,
        name=project.name,
        key=project.key,
        owner_id=project.owner_id,
        my_role=ctx.my_role,
        can_write=ctx.can_write,
    )


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    user: User = Depends(require_role(roles.PLATFORM_MEMBER)),
    db: AsyncSession = Depends(get_db),
) -> ProjectOut:
    try:
        ctx = await project_service.create_project(db, user, body.name, body.key)
    except DuplicateProjectKey as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="项目标识已存在") from exc
    return _out(ctx)


@router.get("", response_model=list[ProjectOut])
async def list_projects(
    user: User = Depends(require_role(roles.PLATFORM_MEMBER, roles.PLATFORM_READONLY)),
    db: AsyncSession = Depends(get_db),
) -> list[ProjectOut]:
    contexts = await project_service.list_projects(db, user)
    return [_out(ctx) for ctx in contexts]


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(ctx: ProjectContext = Depends(project_access())) -> ProjectOut:
    return _out(ctx)


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(
    body: ProjectUpdate,
    ctx: ProjectContext = Depends(project_access(write=True)),
    db: AsyncSession = Depends(get_db),
) -> ProjectOut:
    project = await project_service.rename_project(db, ctx.project, body.name)
    ctx.project = project
    return _out(ctx)


@router.get("/{project_id}/members", response_model=list[MemberOut])
async def list_members(
    ctx: ProjectContext = Depends(project_access()),
    db: AsyncSession = Depends(get_db),
) -> list[MemberOut]:
    rows = await project_service.list_members(db, ctx.project.id)
    return [
        MemberOut(user_id=member.user_id, username=username, role=member.role)
        for member, username in rows
    ]


@router.post(
    "/{project_id}/members",
    response_model=MemberOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_member(
    body: MemberCreate,
    ctx: ProjectContext = Depends(project_access()),
    db: AsyncSession = Depends(get_db),
) -> MemberOut:
    try:
        member = await project_service.add_member(db, ctx, body.username, body.role)
    except ProjectDenied as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有负责人或管理员可以管理成员",
        ) from exc
    except InvalidMemberRole as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="成员角色无效",
        ) from exc
    except UserNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        ) from exc
    except AlreadyMember as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户已是项目成员",
        ) from exc
    return MemberOut(user_id=member.user_id, username=body.username, role=member.role)
