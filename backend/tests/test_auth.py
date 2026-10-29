import asyncio

from app.core.config import get_settings


async def _register(client, username: str, password: str = "password1") -> dict:
    response = await client.post(
        "/api/auth/register",
        json={"username": username, "password": password},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _login(client, username: str, password: str = "password1") -> dict:
    response = await client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    return body


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_login_refresh_rotation_logout_and_access_expiry(client):
    settings = get_settings()
    original = settings.access_token_expire_seconds
    settings.access_token_expire_seconds = 10
    try:
        await _register(client, "alice")
        tokens = await _login(client, "alice")

        alive = await client.get("/api/auth/me", headers=_auth(tokens["access_token"]))
        assert alive.status_code == 200

        await asyncio.sleep(11)
        expired = await client.get("/api/auth/me", headers=_auth(tokens["access_token"]))
        assert expired.status_code == 401

        refreshed = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert refreshed.status_code == 200, refreshed.text
        new_tokens = refreshed.json()
        reused = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert reused.status_code == 401

        logout = await client.post(
            "/api/auth/logout",
            headers=_auth(new_tokens["access_token"]),
            json={"refresh_token": new_tokens["refresh_token"]},
        )
        assert logout.status_code == 204
        after_logout = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": new_tokens["refresh_token"]},
        )
        assert after_logout.status_code == 401
    finally:
        settings.access_token_expire_seconds = original
