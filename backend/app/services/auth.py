from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import roles
from app.core.config import get_settings
from app.core.redis import get_redis
from app.core.security import (
    TokenError,
    create_token,
    decode_token,
    hash_password,
    remaining_ttl,
    verify_password,
)
from app.models.user import User


class DuplicateUsername(Exception):
    pass


class InvalidCredentials(Exception):
    pass


async def register(session: AsyncSession, username: str, password: str) -> User:
    existing = await session.scalar(select(User).where(User.username == username))
    if existing is not None:
        raise DuplicateUsername
    count = await session.scalar(select(func.count()).select_from(User))
    user = User(
        username=username,
        password_hash=hash_password(password),
        role=roles.PLATFORM_ADMIN if count == 0 else roles.PLATFORM_MEMBER,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate(session: AsyncSession, username: str, password: str) -> User:
    user = await session.scalar(select(User).where(User.username == username))
    if user is None or not verify_password(password, user.password_hash):
        raise InvalidCredentials
    return user


async def issue_token_pair(user_id: int) -> tuple[str, str]:
    settings = get_settings()
    access, _ = create_token(user_id, "access", settings.access_token_expire_seconds)
    refresh, jti = create_token(user_id, "refresh", settings.refresh_token_expire_seconds)
    await get_redis().set(
        f"refresh:{jti}",
        str(user_id),
        ex=settings.refresh_token_expire_seconds,
    )
    return access, refresh


async def _blacklist(payload: dict, *, drop_refresh: bool) -> None:
    client = get_redis()
    if drop_refresh:
        await client.delete(f"refresh:{payload['jti']}")
    ttl = remaining_ttl(payload)
    if ttl > 0:
        await client.set(f"blacklist:{payload['jti']}", "1", ex=ttl)


async def refresh_tokens(refresh_token: str) -> tuple[str, str]:
    payload = decode_token(refresh_token, "refresh")
    jti = payload["jti"]
    client = get_redis()
    if await client.exists(f"blacklist:{jti}"):
        raise TokenError("令牌已失效")
    if not await client.exists(f"refresh:{jti}"):
        raise TokenError("令牌已失效")
    user_id = int(payload["sub"])
    await _blacklist(payload, drop_refresh=True)
    return await issue_token_pair(user_id)


async def logout(refresh_token: str, access_token: str | None = None) -> None:
    payload = decode_token(refresh_token, "refresh")
    await _blacklist(payload, drop_refresh=True)
    if not access_token:
        return
    try:
        access_payload = decode_token(access_token, "access")
    except TokenError:
        return
    await _blacklist(access_payload, drop_refresh=False)
