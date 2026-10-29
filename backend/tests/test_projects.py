async def _register(client, username: str) -> dict:
    response = await client.post(
        "/api/auth/register",
        json={"username": username, "password": "password1"},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _login(client, username: str) -> dict[str, str]:
    response = await client.post(
        "/api/auth/login",
        json={"username": username, "password": "password1"},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_project_isolation(client):
    admin = await _register(client, "admin_user")
    assert admin["role"] == "admin"
    owner = await _register(client, "owner_user")
    assert owner["role"] == "member"
    await _register(client, "outsider")

    admin_headers = await _login(client, "admin_user")
    owner_headers = await _login(client, "owner_user")
    outsider_headers = await _login(client, "outsider")

    created = await client.post(
        "/api/projects",
        headers=owner_headers,
        json={"name": "项目1", "key": "project-1"},
    )
    assert created.status_code == 201, created.text
    project_id = created.json()["id"]

    denied = await client.get(f"/api/projects/{project_id}", headers=outsider_headers)
    assert denied.status_code == 403

    added = await client.post(
        f"/api/projects/{project_id}/members",
        headers=owner_headers,
        json={"username": "outsider", "role": "readonly"},
    )
    assert added.status_code == 201, added.text

    readable = await client.get(f"/api/projects/{project_id}", headers=outsider_headers)
    assert readable.status_code == 200
    forbidden = await client.patch(
        f"/api/projects/{project_id}",
        headers=outsider_headers,
        json={"name": "只读改名"},
    )
    assert forbidden.status_code == 403
    unchanged = await client.get(f"/api/projects/{project_id}", headers=owner_headers)
    assert unchanged.json()["name"] == "项目1"

    renamed = await client.patch(
        f"/api/projects/{project_id}",
        headers=admin_headers,
        json={"name": "管理员改名"},
    )
    assert renamed.status_code == 200, renamed.text
    assert renamed.json()["name"] == "管理员改名"
    assert renamed.json()["can_write"] is True
