from app.extensions import db
from app.models.building import Building
from app.models.project import Project
from app.services.pynite_service import PyniteModelBuilder
from tests.conftest import auth_header


def make_building(user, name="Multi-floor tower"):
  project = Project(name="Multi-floor project", user_id=user.id)
  db.session.add(project)
  db.session.flush()
  building = Building(
    name=name,
    project_id=project.id,
    width=12,
    length=10,
    height=15,
    total_floors=5,
  )
  db.session.add(building)
  db.session.commit()
  return building


def floor_payload(number, pillar_width, beam_width, floor_id=None):
  floor_id = floor_id or f"floor-{number}"
  p1 = f"{floor_id}-c1"
  p2 = f"{floor_id}-c2"
  return {
    "id": floor_id,
    "floorNumber": number,
    "name": f"Floor {number}",
    "elevation": (number - 1) * 3,
    "height": 3,
    "pillars": [
      {
        "id": p1,
        "name": "C1",
        "stackId": "stack-c1",
        "x": 2,
        "y": 2,
        "width": pillar_width,
        "depth": pillar_width,
        "height": 3,
      },
      {
        "id": p2,
        "name": "C2",
        "stackId": "stack-c2",
        "x": 10,
        "y": 2,
        "width": pillar_width,
        "depth": pillar_width,
        "height": 3,
      },
    ],
    "beams": [{
      "id": f"{floor_id}-b3",
      "name": "B3",
      "startPillarId": p1,
      "endPillarId": p2,
      "startX": 2,
      "startY": 2,
      "endX": 10,
      "endY": 2,
      "width": beam_width,
      "depth": 0.6,
    }],
    "slabs": [{
      "id": f"{floor_id}-slab",
      "name": "S1",
      "thickness": 0.15,
      "area": 80,
    }],
    "walls": [],
    "openings": [],
    "stairs": [],
  }


def test_floor_owned_dimensions_round_trip_and_delete(client, engineer_user):
  building = make_building(engineer_user)
  headers, _ = auth_header(client, "eng@test.com", "Engineer1")
  floors = [
    floor_payload(1, 0.45, 0.25),
    floor_payload(2, 0.45, 0.30),
    floor_payload(3, 0.40, 0.27),
    floor_payload(4, 0.30, 0.23),
    floor_payload(5, 0.30, 0.23),
  ]
  saved = client.put(
    f"/api/v1/buildings/{building.id}/structure",
    headers=headers,
    json={"structure": {"schemaVersion": 2, "floors": floors}, "version": 0},
  )
  assert saved.status_code == 200, saved.get_json()
  assert saved.get_json()["data"]["version"] == 1

  loaded = client.get(f"/api/v1/buildings/{building.id}/structure", headers=headers)
  assert loaded.status_code == 200
  data = loaded.get_json()["data"]
  by_number = {floor["floorNumber"]: floor for floor in data["floors"]}
  assert by_number[2]["pillars"][1]["width"] == 0.45
  assert by_number[4]["pillars"][1]["width"] == 0.30
  assert by_number[2]["beams"][0]["width"] == 0.30
  assert by_number[5]["beams"][0]["width"] == 0.23
  assert len({floor["id"] for floor in data["floors"]}) == 5

  remaining = [floor for floor in floors if floor["floorNumber"] != 3]
  removed = client.put(
    f"/api/v1/buildings/{building.id}/structure",
    headers=headers,
    json={"structure": {"schemaVersion": 2, "floors": remaining}, "version": 1},
  )
  assert removed.status_code == 200
  reloaded = client.get(f"/api/v1/buildings/{building.id}/structure", headers=headers)
  assert [floor["floorNumber"] for floor in reloaded.get_json()["data"]["floors"]] == [1, 2, 4, 5]


def test_structure_rejects_cross_floor_beam_and_stale_revision(client, engineer_user):
  building = make_building(engineer_user)
  headers, _ = auth_header(client, "eng@test.com", "Engineer1")
  first = floor_payload(1, 0.4, 0.25)
  second = floor_payload(2, 0.4, 0.25)
  second["beams"][0]["endPillarId"] = first["pillars"][1]["id"]
  invalid = client.put(
    f"/api/v1/buildings/{building.id}/structure",
    headers=headers,
    json={"structure": {"floors": [first, second]}, "version": 0},
  )
  assert invalid.status_code == 400
  assert "same floor" in invalid.get_json()["message"].lower()

  valid = client.put(
    f"/api/v1/buildings/{building.id}/structure",
    headers=headers,
    json={"structure": {"floors": [first]}, "version": 0},
  )
  assert valid.status_code == 200
  stale = client.put(
    f"/api/v1/buildings/{building.id}/structure",
    headers=headers,
    json={"structure": {"floors": [first]}, "version": 0},
  )
  assert stale.status_code == 409


def test_structure_requires_building_ownership(client, viewer_user, engineer_user):
  building = make_building(engineer_user)
  headers, _ = auth_header(client, "viewer@test.com", "Viewer12")
  response = client.get(f"/api/v1/buildings/{building.id}/structure", headers=headers)
  assert response.status_code == 403


def test_pynite_geometry_keeps_floor_specific_sections(app, engineer_user):
  building = make_building(engineer_user)
  from app.services.structure_sync_service import StructureSyncService

  floors = [floor_payload(1, 0.45, 0.30), floor_payload(2, 0.30, 0.23)]
  StructureSyncService.save(building, {"floors": floors}, 0)
  db.session.commit()
  result = PyniteModelBuilder.build(building, run_analysis=False)
  pillars = [member for member in result["members"] if member["memberType"] == "pillar"]
  assert sorted(member["width"] for member in pillars) == [0.3, 0.3, 0.45, 0.45]
  assert {member["floorId"] for member in pillars} == {"floor-1", "floor-2"}
  analyzed = PyniteModelBuilder.build(building, run_analysis=True)
  assert analyzed["available"] is True
  if analyzed["analyzed"]:
    assert all("result" in member for member in analyzed["members"])
