from flask import request
from app.extensions import db
from app.models.project import Project
from app.access import get_project_for_user, current_user_or_401
from app.services.building_service import BuildingService
from app.utils import success_response, error_response, validate_required_fields


class ProjectController:
  @staticmethod
  def get_projects():
    current, err = current_user_or_401()
    if err:
      return err
    if getattr(current, "role", None) == "admin":
      projects = Project.query.all()
    else:
      projects = Project.query.filter_by(user_id=current.id).all()
    return success_response([p.to_dict(include_buildings=True) for p in projects])

  @staticmethod
  def get_project(project_id):
    _, project, err = get_project_for_user(project_id)
    if err:
      return err
    return success_response(project.to_dict(include_buildings=True))

  @staticmethod
  def create_project():
    current, err = current_user_or_401()
    if err:
      return err

    data = request.get_json(silent=True) or {}
    error = validate_required_fields(data, ["name"])
    if error:
      return error_response(error, 400)

    project = Project(
      name=data["name"],
      description=data.get("description"),
      location=data.get("location"),
      status=data.get("status", "planning"),
      user_id=current.id,
    )
    db.session.add(project)
    db.session.commit()

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
    _, project, err = get_project_for_user(project_id)
    if err:
      return err

    data = request.get_json(silent=True) or {}
    for field in ["name", "description", "location", "status"]:
      if field in data:
        setattr(project, field, data[field])

    db.session.commit()
    return success_response(project.to_dict(), "Project updated")

  @staticmethod
  def delete_project(project_id):
    _, project, err = get_project_for_user(project_id)
    if err:
      return err

    db.session.delete(project)
    db.session.commit()
    return success_response(message="Project deleted")
