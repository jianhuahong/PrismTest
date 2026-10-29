import os
from urllib.parse import urlparse

os.environ.setdefault(
    "DATABASE_URL",
    "mysql+aiomysql://root:prism_root@127.0.0.1:3307/prism_test",
)
os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:6380/1")
os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-characters-long")

import pymysql
import pytest
from alembic import command
from alembic.config import Config
from app.core.database import engine
from app.core.redis import get_redis
from app.main import app
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text


def _ensure_database() -> None:
    parsed = urlparse(os.environ["DATABASE_URL"])
    name = parsed.path.lstrip("/")
    connection = pymysql.connect(
        host=parsed.hostname or "127.0.0.1",
        port=parsed.port or 3306,
        user=parsed.username,
        password=parsed.password,
        database="mysql",
        charset="utf8mb4",
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        connection.commit()
    finally:
        connection.close()


@pytest.fixture(scope="session", autouse=True)
def migrated() -> None:
    _ensure_database()
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
async def client():
    async with engine.begin() as connection:
        await connection.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        await connection.execute(text("TRUNCATE TABLE project_members"))
        await connection.execute(text("TRUNCATE TABLE projects"))
        await connection.execute(text("TRUNCATE TABLE users"))
        await connection.execute(text("SET FOREIGN_KEY_CHECKS=1"))
    await get_redis().flushdb()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
