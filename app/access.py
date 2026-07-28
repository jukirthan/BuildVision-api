"""Shared project ownership / admin access helpers."""

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


def can_access_project(user, project):
  if not user or not project:
    return False
  if getattr(user, "role", None) == "admin":
    return True
  return project.user_id == user.id


def get_project_for_user(project_id):
  user, err = current_user_or_401()
  if err:
    return None, None, err
  project = Project.query.get(project_id)
  if not project:
    return None, None, error_response("Project not found", 404)
  if not can_access_project(user, project):
    return None, None, error_response("Forbidden", 403)
  return user, project, None


def get_building_for_user(building_id):
  user, err = current_user_or_401()
  if err:
    return None, None, err
  building = Building.query.get(building_id)
  if not building:
    return None, None, error_response("Building not found", 404)
  project = Project.query.get(building.project_id)
  if not project:
    return None, None, error_response("Project not found", 404)
  if not can_access_project(user, project):
    return None, None, error_response("Forbidden", 403)
  return user, building, None


def get_floor_for_user(floor_id):
  user, err = current_user_or_401()
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
  if not can_access_project(user, project):
    return None, None, error_response("Forbidden", 403)
  return user, floor, None
