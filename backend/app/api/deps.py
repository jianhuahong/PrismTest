from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import roles
from app.core.database import get_db
from app.core.redis import get_redis
from app.core.security import TokenError, decode_token
from app.models.user import User
from app.services import projects as project_service
from app.services.projects import ProjectContext, ProjectDenied, ProjectNotFound

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")
    try:
        payload = decode_token(credentials.credentials, "access")
    except TokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    if await get_redis().exists(f"blacklist:{payload['jti']}"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌已失效")
    user = await db.get(User, int(payload["sub"]))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    return user


def require_role(*allowed: str):
    async def checker(user: User = Depends(get_current_user)) -> User:
        if user.role == roles.PLATFORM_ADMIN or user.role in allowed:
            return user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")

    return checker


def project_access(write: bool = False):
    async def dependency(
        project_id: int,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> ProjectContext:
        try:
            ctx = await project_service.get_access(db, user, project_id)
        except ProjectNotFound as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="项目不存在",
            ) from exc
        except ProjectDenied as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问该项目",
            ) from exc
        if write and not ctx.can_write:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只读成员不能修改",
            )
        return ctx

    return dependency
