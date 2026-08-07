from app.extensions import db
from app.models.building import Building
from app.models.project import Project
from tests.conftest import auth_header


def make_building(user, name="Test building"):
  project = Project(name="Test project", user_id=user.id)
  db.session.add(project)
  db.session.flush()
  building = Building(name=name, project_id=project.id)
  db.session.add(building)
  db.session.commit()
  return building


def test_design_round_trip_and_optimistic_conflict(client, engineer_user):
  building = make_building(engineer_user)
  headers, _ = auth_header(client, "eng@test.com", "Engineer1")
  snapshot = {"schemaVersion": 1, "pillars": [{"id": "p-1"}]}

  saved = client.put(
    f"/api/v1/buildings/{building.id}/design",
    headers=headers,
    json={"snapshot": snapshot, "version": 0},
  )
  assert saved.status_code == 200
  assert saved.get_json()["data"]["version"] == 1

  loaded = client.get(
    f"/api/v1/buildings/{building.id}/design", headers=headers
  )
  assert loaded.status_code == 200
  assert loaded.get_json()["data"] == {"snapshot": snapshot, "version": 1}

  stale = client.put(
    f"/api/v1/buildings/{building.id}/design",
    headers=headers,
    json={"snapshot": {"schemaVersion": 1}, "version": 0},
  )
  assert stale.status_code == 409


def test_viewer_cannot_save_design(client, viewer_user):
  building = make_building(viewer_user)
  headers, _ = auth_header(client, "viewer@test.com", "Viewer12")

  response = client.put(
    f"/api/v1/buildings/{building.id}/design",
    headers=headers,
    json={"snapshot": {"schemaVersion": 1}, "version": 0},
  )
  assert response.status_code == 403
