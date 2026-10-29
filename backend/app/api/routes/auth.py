from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import bearer_scheme, get_current_user
from app.core.database import get_db
from app.core.security import TokenError
from app.models.user import User
from app.schemas.auth import LoginIn, LogoutIn, RefreshIn, RegisterIn, TokenOut, UserOut
from app.services import auth as auth_service
from app.services.auth import DuplicateUsername, InvalidCredentials

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterIn, db: AsyncSession = Depends(get_db)) -> User:
    try:
        return await auth_service.register(db, body.username, body.password)
    except DuplicateUsername as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名已存在") from exc


@router.post("/login", response_model=TokenOut)
async def login(body: LoginIn, db: AsyncSession = Depends(get_db)) -> TokenOut:
    try:
        user = await auth_service.authenticate(db, body.username, body.password)
    except InvalidCredentials as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        ) from exc
    access, refresh = await auth_service.issue_token_pair(user.id)
    return TokenOut(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenOut)
async def refresh(body: RefreshIn) -> TokenOut:
    try:
        access, refresh_token = await auth_service.refresh_tokens(body.refresh_token)
    except TokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return TokenOut(access_token=access, refresh_token=refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: LogoutIn,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> None:
    access = credentials.credentials if credentials is not None else None
    try:
        await auth_service.logout(body.refresh_token, access)
    except TokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> User:
    return user
