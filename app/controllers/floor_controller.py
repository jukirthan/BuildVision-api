from flask import request
from app.models.building import Building
from app.models.project import Project
from app.middleware import get_current_user
from app.services.floor_service import FloorService
from app.utils import success_response, error_response, validate_required_fields


class FloorController:
  @staticmethod
  def _check_building_access(building_id):
    current = get_current_user()
    building = Building.query.get(building_id)
    if not building:
      return None, error_response("Building not found", 404)
    project = Project.query.get(building.project_id)
    if project.user_id != current.id:
      return None, error_response("Forbidden", 403)
    return building, None

  @staticmethod
  def get_floors(building_id):
    _, err = FloorController._check_building_access(building_id)
    if err:
      return err
    floors = FloorService.get_floors_by_building(building_id)
    return success_response([f.to_dict() for f in floors])

  @staticmethod
  def get_floor(floor_id):
    floor = FloorService.get_floor_by_id(floor_id)
    if not floor:
      return error_response("Floor not found", 404)
    _, err = FloorController._check_building_access(floor.building_id)
    if err:
      return err
    return success_response(floor.to_dict(include_components=True))

  @staticmethod
  def create_floor(building_id):
    _, err = FloorController._check_building_access(building_id)
    if err:
      return err

    data = request.get_json() or {}
    error = validate_required_fields(data, ["name", "floor_number"])
    if error:
      return error_response(error, 400)

    floor, err_msg = FloorService.create_floor(data, building_id)
    if err_msg:
      return error_response(err_msg, 404)
    return success_response(floor.to_dict(), "Floor created", 201)

  @staticmethod
  def update_floor(floor_id):
    floor = FloorService.get_floor_by_id(floor_id)
    if not floor:
      return error_response("Floor not found", 404)
    _, err = FloorController._check_building_access(floor.building_id)
    if err:
      return err

    data = request.get_json() or {}
    floor = FloorService.update_floor(floor, data)
    return success_response(floor.to_dict(), "Floor updated")

  @staticmethod
  def delete_floor(floor_id):
    floor = FloorService.get_floor_by_id(floor_id)
    if not floor:
      return error_response("Floor not found", 404)
    _, err = FloorController._check_building_access(floor.building_id)
    if err:
      return err

    FloorService.delete_floor(floor)
    return success_response(message="Floor deleted")
