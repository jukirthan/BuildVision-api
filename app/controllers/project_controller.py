from flask import request
from app.extensions import db
from app.models.project import Project
from app.middleware import get_current_user
from app.utils import success_response, error_response, validate_required_fields


class ProjectController:
  @staticmethod
  def get_projects():
    current = get_current_user()
    if not current:
      return error_response("Unauthorized", 401)
    projects = Project.query.filter_by(user_id=current.id).all()
    return success_response([p.to_dict() for p in projects])

  @staticmethod
  def get_project(project_id):
    current = get_current_user()
    project = Project.query.get(project_id)
    if not project:
      return error_response("Project not found", 404)
    if project.user_id != current.id:
      return error_response("Forbidden", 403)
    return success_response(project.to_dict(include_buildings=True))

  @staticmethod
  def create_project():
    current = get_current_user()
    if not current:
      return error_response("Unauthorized", 401)

    data = request.get_json() or {}
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
    return success_response(project.to_dict(), "Project created", 201)

  @staticmethod
  def update_project(project_id):
    current = get_current_user()
    project = Project.query.get(project_id)
    if not project:
      return error_response("Project not found", 404)
    if project.user_id != current.id:
      return error_response("Forbidden", 403)

    data = request.get_json() or {}
    for field in ["name", "description", "location", "status"]:
      if field in data:
        setattr(project, field, data[field])

    db.session.commit()
    return success_response(project.to_dict(), "Project updated")

  @staticmethod
  def delete_project(project_id):
    current = get_current_user()
    project = Project.query.get(project_id)
    if not project:
      return error_response("Project not found", 404)
    if project.user_id != current.id:
      return error_response("Forbidden", 403)

    db.session.delete(project)
    db.session.commit()
    return success_response(message="Project deleted")
