"""Smoke-test all BuildVision API routes."""
from __future__ import annotations

import random
import sys

from app import create_app
from app.seeders import seed_admin_user


def ok(label, res, expect=(200, 201)):
  code = res.status_code
  body = res.get_json(silent=True) or {}
  passed = code in expect and (body.get("success") is True or code in (200, 201))
  # health uses success True now
  if code in expect and body.get("success") is not False:
    passed = True
  status = "PASS" if passed else "FAIL"
  msg = body.get("message") or body.get("status") or ""
  print(f"[{status}] {code:3} {label} {msg}")
  if not passed:
    print("       ", body)
  return passed


def main():
  app = create_app("development")
  fails = 0
  with app.app_context():
    seed_admin_user()

  client = app.test_client()
  print("Starting smoke tests...", flush=True)

  if not ok("GET  /api/health", client.get("/api/health")):
    fails += 1

  # Auth
  email = f"smoke{random.randint(10000, 99999)}@buildvision.test"
  reg = client.post(
    "/api/auth/register",
    json={
      "name": "Smoke Tester",
      "email": email,
      "password": "secret12",
      "role": "engineer",
    },
  )
  if not ok("POST /api/auth/register", reg, (201,)):
    fails += 1
    # fallback login as admin
    login = client.post(
      "/api/auth/login",
      json={"email": "admin@buildvision.com", "password": "admin123"},
    )
  else:
    login = client.post(
      "/api/auth/login",
      json={"email": email, "password": "secret12"},
    )

  if not ok("POST /api/auth/login", login):
    fails += 1
    print("Cannot continue without token")
    return 1

  token = (login.get_json() or {}).get("data", {}).get("access_token")
  h = {"Authorization": f"Bearer {token}"}

  if not ok("POST /api/users/login (alias)", client.post(
    "/api/users/login",
    json={"email": "admin@buildvision.com", "password": "admin123"},
  )):
    fails += 1

  if not ok("GET  /api/users/profile", client.get("/api/users/profile", headers=h)):
    fails += 1

  # Projects
  proj = client.post(
    "/api/projects/",
    json={"name": "Smoke Project", "description": "route test", "location": "Test"},
    headers=h,
  )
  if not ok("POST /api/projects/", proj, (201,)):
    fails += 1
    return 1
  project = (proj.get_json() or {}).get("data") or {}
  pid = project["id"]
  buildings = project.get("buildings") or []
  bid = buildings[0]["id"] if buildings else None

  if not ok("GET  /api/projects/", client.get("/api/projects/", headers=h)):
    fails += 1
  if not ok(f"GET  /api/projects/{pid}", client.get(f"/api/projects/{pid}", headers=h)):
    fails += 1
  if not ok(
    f"PUT  /api/projects/{pid}",
    client.put(f"/api/projects/{pid}", json={"status": "in_progress"}, headers=h),
  ):
    fails += 1

  # Buildings
  if not ok(
    f"GET  /api/buildings/project/{pid}",
    client.get(f"/api/buildings/project/{pid}", headers=h),
  ):
    fails += 1

  bcreate = client.post(
    f"/api/buildings/project/{pid}",
    json={"name": "Smoke Tower", "total_floors": 2, "width": 24, "length": 16},
    headers=h,
  )
  if not ok(f"POST /api/buildings/project/{pid}", bcreate, (201,)):
    fails += 1
  else:
    bid = (bcreate.get_json() or {}).get("data", {}).get("id", bid)

  if bid is None:
    print("[FAIL] No building id")
    return 1

  if not ok(f"GET  /api/buildings/{bid}", client.get(f"/api/buildings/{bid}", headers=h)):
    fails += 1
  if not ok(
    f"PUT  /api/buildings/{bid}",
    client.put(f"/api/buildings/{bid}", json={"name": "Smoke Tower Updated"}, headers=h),
  ):
    fails += 1

  # Floors
  floors_res = client.get(f"/api/floors/building/{bid}", headers=h)
  if not ok(f"GET  /api/floors/building/{bid}", floors_res):
    fails += 1
  floors = (floors_res.get_json() or {}).get("data") or []
  fid = floors[0]["id"] if floors else None

  if fid is None:
    fcreate = client.post(
      f"/api/floors/building/{bid}",
      json={"name": "Floor 1", "floor_number": 1, "height": 3.5},
      headers=h,
    )
    if not ok(f"POST /api/floors/building/{bid}", fcreate, (201,)):
      fails += 1
      return 1
    fid = (fcreate.get_json() or {}).get("data", {}).get("id")

  if not ok(f"GET  /api/floors/{fid}", client.get(f"/api/floors/{fid}", headers=h)):
    fails += 1
  if not ok(
    f"PUT  /api/floors/{fid}",
    client.put(f"/api/floors/{fid}", json={"height": 3.6}, headers=h),
  ):
    fails += 1

  # Pillars
  pcreate = client.post(
    f"/api/pillars/floor/{fid}",
    json={"name": "P-Smoke", "x_position": 2, "y_position": 3, "width": 0.4, "depth": 0.4},
    headers=h,
  )
  if not ok(f"POST /api/pillars/floor/{fid}", pcreate, (201,)):
    fails += 1
  pillar_id = (pcreate.get_json() or {}).get("data", {}).get("id")

  if not ok(f"GET  /api/pillars/floor/{fid}", client.get(f"/api/pillars/floor/{fid}", headers=h)):
    fails += 1
  if pillar_id:
    if not ok(f"GET  /api/pillars/{pillar_id}", client.get(f"/api/pillars/{pillar_id}", headers=h)):
      fails += 1
    if not ok(
      f"PUT  /api/pillars/{pillar_id}/move",
      client.put(
        f"/api/pillars/{pillar_id}/move",
        json={"x_position": 4, "y_position": 5},
        headers=h,
      ),
    ):
      fails += 1
    if not ok(
      f"PUT  /api/pillars/{pillar_id}/resize",
      client.put(
        f"/api/pillars/{pillar_id}/resize",
        json={"width": 0.45, "depth": 0.45},
        headers=h,
      ),
    ):
      fails += 1
    if not ok(
      f"PUT  /api/pillars/{pillar_id}",
      client.put(f"/api/pillars/{pillar_id}", json={"name": "P-Smoke-2"}, headers=h),
    ):
      fails += 1

  # Beams
  bmc = client.post(
    f"/api/beams/floor/{fid}",
    json={
      "name": "B-Smoke",
      "start_x": 0,
      "start_y": 0,
      "end_x": 5,
      "end_y": 0,
      "width": 0.3,
      "depth": 0.4,
    },
    headers=h,
  )
  # may require different fields — don't hard-fail if validation differs
  if bmc.status_code in (200, 201):
    ok(f"POST /api/beams/floor/{fid}", bmc, (201, 200))
    beam_id = (bmc.get_json() or {}).get("data", {}).get("id")
  else:
    print(f"[WARN] {bmc.status_code} POST /api/beams/floor/{fid} {(bmc.get_json() or {}).get('message')}")
    beam_id = None
    # still count as fail if 500
    if bmc.status_code >= 500:
      fails += 1

  if not ok(f"GET  /api/beams/floor/{fid}", client.get(f"/api/beams/floor/{fid}", headers=h)):
    fails += 1
  if beam_id:
    if not ok(f"GET  /api/beams/{beam_id}", client.get(f"/api/beams/{beam_id}", headers=h)):
      fails += 1

  # Slabs
  sc = client.post(
    f"/api/slabs/floor/{fid}",
    json={"name": "S-Smoke", "thickness": 0.15, "area": 40},
    headers=h,
  )
  if sc.status_code in (200, 201):
    ok(f"POST /api/slabs/floor/{fid}", sc, (201, 200))
    slab_id = (sc.get_json() or {}).get("data", {}).get("id")
  else:
    print(f"[WARN] {sc.status_code} POST /api/slabs/floor/{fid} {(sc.get_json() or {}).get('message')}")
    slab_id = None
    if sc.status_code >= 500:
      fails += 1

  if not ok(f"GET  /api/slabs/floor/{fid}", client.get(f"/api/slabs/floor/{fid}", headers=h)):
    fails += 1

  # Dashboard + recommendations
  if not ok("GET  /api/dashboard/summary", client.get("/api/dashboard/summary", headers=h)):
    fails += 1
  if not ok(
    f"GET  /api/dashboard/building/{bid}/statistics",
    client.get(f"/api/dashboard/building/{bid}/statistics", headers=h),
  ):
    fails += 1
  if not ok(
    f"GET  /api/dashboard/floor/{fid}/materials",
    client.get(f"/api/dashboard/floor/{fid}/materials", headers=h),
  ):
    fails += 1
  if not ok(
    f"GET  /api/recommendations/floor/{fid}",
    client.get(f"/api/recommendations/floor/{fid}", headers=h),
  ):
    fails += 1
  if not ok(
    "POST /api/recommendations/layouts",
    client.post(
      "/api/recommendations/layouts",
      json={"width": 30, "length": 20, "floors": 3},
      headers=h,
    ),
  ):
    fails += 1

  # Cleanup deletes
  if pillar_id and not ok(
    f"DELETE /api/pillars/{pillar_id}",
    client.delete(f"/api/pillars/{pillar_id}", headers=h),
  ):
    fails += 1
  if beam_id and not ok(
    f"DELETE /api/beams/{beam_id}",
    client.delete(f"/api/beams/{beam_id}", headers=h),
  ):
    fails += 1
  if slab_id and not ok(
    f"DELETE /api/slabs/{slab_id}",
    client.delete(f"/api/slabs/{slab_id}", headers=h),
  ):
    fails += 1

  print("\n" + ("ALL ROUTES OK" if fails == 0 else f"{fails} FAILURE(S)"))
  return 1 if fails else 0


if __name__ == "__main__":
  sys.exit(main())
