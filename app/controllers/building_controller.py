from flask import request
from app.models.project import Project
from app.middleware import get_current_user
from app.services.building_service import BuildingService
from app.utils import success_response, error_response, validate_required_fields


class BuildingController:
  @staticmethod
  def _check_project_access(project_id):
    current = get_current_user()
    project = Project.query.get(project_id)
    if not project:
      return None, error_response("Project not found", 404)
    if project.user_id != current.id:
      return None, error_response("Forbidden", 403)
    return project, None

  @staticmethod
  def get_buildings(project_id):
    _, err = BuildingController._check_project_access(project_id)
    if err:
      return err
    buildings = BuildingService.get_buildings_by_project(project_id)
    return success_response([b.to_dict() for b in buildings])

  @staticmethod
  def get_building(building_id):
    building = BuildingService.get_building_by_id(building_id)
    if not building:
      return error_response("Building not found", 404)
    _, err = BuildingController._check_project_access(building.project_id)
    if err:
      return err
    return success_response(building.to_dict(include_floors=True))

  @staticmethod
  def create_building(project_id):
    _, err = BuildingController._check_project_access(project_id)
    if err:
      return err

    data = request.get_json() or {}
    error = validate_required_fields(data, ["name"])
    if error:
      return error_response(error, 400)

    building, err_msg = BuildingService.create_building(data, project_id)
    if err_msg:
      return error_response(err_msg, 404)
    return success_response(building.to_dict(), "Building created", 201)

  @staticmethod
  def update_building(building_id):
    building = BuildingService.get_building_by_id(building_id)
    if not building:
      return error_response("Building not found", 404)
    _, err = BuildingController._check_project_access(building.project_id)
    if err:
      return err

    data = request.get_json() or {}
    building = BuildingService.update_building(building, data)
    return success_response(building.to_dict(), "Building updated")

  @staticmethod
  def delete_building(building_id):
    building = BuildingService.get_building_by_id(building_id)
    if not building:
      return error_response("Building not found", 404)
    _, err = BuildingController._check_project_access(building.project_id)
    if err:
      return err

    BuildingService.delete_building(building)
    return success_response(message="Building deleted")
