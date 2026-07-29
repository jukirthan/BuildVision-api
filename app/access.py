"""Shared project ownership / admin access helpers."""

from flask_jwt_extended import get_jwt, get_jwt_identity

from app.models.project import Project
from app.models.building import Building
from app.models.floor import Floor
from app.middleware import get_current_user
from app.utils import error_response


def current_user_or_401():
  user = get_current_user()
  if not user:
    return None, error_response("Unauthorized", 401)
  return user, None


def current_identity_or_401():
  """Caller id + role from the JWT — no remote user lookup."""
  user_id = get_jwt_identity()
  if not user_id:
    return None, error_response("Unauthorized", 401)
  claims = get_jwt() or {}
  return {
    "id": int(user_id),
    "role": str(claims.get("role") or "engineer").lower(),
  }, None


def can_access_project(user, project):
  if not user or not project:
    return False
  if isinstance(user, dict):
    role = user.get("role")
    user_id = user.get("id")
  else:
    role = getattr(user, "role", None)
    user_id = getattr(user, "id", None)
  if role == "admin":
    return True
  return project.user_id == user_id


def get_project_for_user(project_id):
  identity, err = current_identity_or_401()
  if err:
    return None, None, err
  project = Project.query.get(project_id)
  if not project:
    return None, None, error_response("Project not found", 404)
  if not can_access_project(identity, project):
    return None, None, error_response("Forbidden", 403)
  return identity, project, None


def get_building_for_user(building_id):
  identity, err = current_identity_or_401()
  if err:
    return None, None, err
  building = Building.query.get(building_id)
  if not building:
    return None, None, error_response("Building not found", 404)
  project = Project.query.get(building.project_id)
  if not project:
    return None, None, error_response("Project not found", 404)
  if not can_access_project(identity, project):
    return None, None, error_response("Forbidden", 403)
  return identity, building, None


def get_floor_for_user(floor_id):
  identity, err = current_identity_or_401()
  if err:
    return None, None, err
  floor = Floor.query.get(floor_id)
  if not floor:
    return None, None, error_response("Floor not found", 404)
  building = Building.query.get(floor.building_id)
  if not building:
    return None, None, error_response("Building not found", 404)
  project = Project.query.get(building.project_id)
  if not project:
    return None, None, error_response("Project not found", 404)
  if not can_access_project(identity, project):
    return None, None, error_response("Forbidden", 403)
  return identity, floor, None
