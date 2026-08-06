from flask import request
from sqlalchemy.orm import selectinload
from app.extensions import db
from app.models.project import Project
from app.access import (
  get_project_for_user,
  current_identity_or_401,
  require_mutate,
)
from app.services.building_service import BuildingService
from app.ttl_cache import projects_cache
from app.utils import success_response, error_response, validate_required_fields


class ProjectController:
  @staticmethod
  def get_projects():
    identity, err = current_identity_or_401()
    if err:
      return err
    cache_key = f"projects:{identity['role']}:{identity['id']}"
    cached = projects_cache.get(cache_key)
    if cached is not None:
      return success_response(cached)

    # selectinload = 2 queries total (projects + buildings), not N+1 lazy joins
    query = Project.query.options(selectinload(Project.buildings))
    if identity["role"] == "admin":
      projects = query.order_by(Project.created_at.desc()).all()
    else:
      projects = (
        query.filter_by(user_id=identity["id"])
        .order_by(Project.created_at.desc())
        .all()
      )
    payload = [p.to_dict(include_buildings=True) for p in projects]
    projects_cache.set(cache_key, payload)
    return success_response(payload)

  @staticmethod
  def get_project(project_id):
    _, project, err = get_project_for_user(project_id)
    if err:
      return err
    project = (
      Project.query.options(selectinload(Project.buildings))
      .filter_by(id=project_id)
      .first()
    )
    if not project:
      return error_response("Project not found", 404)
    return success_response(project.to_dict(include_buildings=True))

  @staticmethod
  def create_project():
    identity, err = current_identity_or_401()
    if err:
      return err
    denied = require_mutate(identity)
    if denied:
      return denied

    data = request.get_json(silent=True) or {}
    error = validate_required_fields(data, ["name"])
    if error:
      return error_response(error, 400)

    project = Project(
      name=data["name"],
      description=data.get("description"),
      location=data.get("location"),
      status=data.get("status", "planning"),
      user_id=identity["id"],
    )
    db.session.add(project)
    db.session.commit()
    projects_cache.invalidate("projects:")

    # Always create a starter building so users can open the planner immediately
    building_name = data.get("building_name") or f"{data['name']} — Building 1"
    BuildingService.create_building(
      {
        "name": building_name,
        "building_type": data.get("building_type", "commercial"),
        "total_floors": data.get("total_floors", 3),
        "width": data.get("width", 30.0),
        "length": data.get("length", 20.0),
      },
      project.id,
    )

    return success_response(
      project.to_dict(include_buildings=True),
      "Project created",
      201,
    )

  @staticmethod
  def update_project(project_id):
    _, project, err = get_project_for_user(project_id, write=True)
    if err:
      return err

    data = request.get_json(silent=True) or {}
    for field in ["name", "description", "location", "status"]:
      if field in data:
        setattr(project, field, data[field])

    db.session.commit()
    projects_cache.invalidate("projects:")
    return success_response(project.to_dict(), "Project updated")

  @staticmethod
  def delete_project(project_id):
    _, project, err = get_project_for_user(project_id, write=True)
    if err:
      return err

    db.session.delete(project)
    db.session.commit()
    projects_cache.invalidate("projects:")
    return success_response(message="Project deleted")
