import time
import uuid

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenError(Exception):
    pass


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_token(user_id: int, token_type: str, ttl_seconds: int) -> tuple[str, str]:
    now = int(time.time())
    jti = str(uuid.uuid4())
    payload = {
        "sub": str(user_id),
        "jti": jti,
        "type": token_type,
        "iat": now,
        "exp": now + ttl_seconds,
    }
    token = jwt.encode(payload, get_settings().secret_key, algorithm="HS256")
    return token, jti


def decode_token(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(token, get_settings().secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise TokenError("令牌无效或已过期") from exc
    if payload.get("type") != expected_type:
        raise TokenError("令牌类型不正确")
    return payload


def remaining_ttl(payload: dict) -> int:
    return int(payload["exp"]) - int(time.time())
