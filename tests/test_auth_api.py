def test_health_legacy_and_v1(client):
  for path in ("/api/health", "/api/v1/health"):
    res = client.get(path)
    assert res.status_code == 200
    body = res.get_json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"


def test_login_and_refresh_keeps_role(client, admin_user):
  res = client.post(
    "/api/auth/login",
    json={"email": "admin@test.com", "password": "Admin123"},
  )
  assert res.status_code == 200
  data = res.get_json()["data"]
  assert data["user"]["role"] == "admin"
  refresh = data["refresh_token"]

  refreshed = client.post(
    "/api/auth/refresh",
    headers={"Authorization": f"Bearer {refresh}"},
  )
  assert refreshed.status_code == 200
  payload = refreshed.get_json()["data"]
  assert payload["role"] == "admin"
  assert payload.get("access_token") or payload.get("token")


def test_v1_login_alias(client, engineer_user):
  res = client.post(
    "/api/v1/auth/login",
    json={"email": "eng@test.com", "password": "Engineer1"},
  )
  assert res.status_code == 200
  assert res.get_json()["success"] is True


def test_viewer_cannot_create_project(client, viewer_user):
  from tests.conftest import auth_header

  headers, _ = auth_header(client, "viewer@test.com", "Viewer12")
  res = client.post(
    "/api/projects/",
    headers=headers,
    json={"name": "Should Fail"},
  )
  assert res.status_code == 403


def test_engineer_can_create_project(client, engineer_user):
  from tests.conftest import auth_header

  headers, _ = auth_header(client, "eng@test.com", "Engineer1")
  res = client.post(
    "/api/projects/",
    headers=headers,
    json={"name": "Tower A", "total_floors": 2},
  )
  assert res.status_code == 201
  assert res.get_json()["data"]["name"] == "Tower A"


def test_weak_password_rejected(client):
  res = client.post(
    "/api/auth/register",
    json={
      "name": "Weak User",
      "email": "weak@test.com",
      "password": "short",
    },
  )
  assert res.status_code == 400
