from flask import request
from app.access import get_building_for_user, get_floor_for_user
from app.services.floor_service import FloorService
from app.utils import success_response, error_response, validate_required_fields


class FloorController:
  @staticmethod
  def get_floors(building_id):
    _, _, err = get_building_for_user(building_id)
    if err:
      return err
    floors = FloorService.get_floors_by_building(building_id)
    return success_response([f.to_dict() for f in floors])

  @staticmethod
  def get_floor(floor_id):
    _, floor, err = get_floor_for_user(floor_id)
    if err:
      return err
    return success_response(floor.to_dict(include_components=True))

  @staticmethod
  def create_floor(building_id):
    _, _, err = get_building_for_user(building_id)
    if err:
      return err

    data = request.get_json(silent=True) or {}
    error = validate_required_fields(data, ["name", "floor_number"])
    if error:
      return error_response(error, 400)

    floor, err_msg = FloorService.create_floor(data, building_id)
    if err_msg:
      return error_response(err_msg, 404)
    return success_response(floor.to_dict(), "Floor created", 201)

  @staticmethod
  def update_floor(floor_id):
    _, floor, err = get_floor_for_user(floor_id)
    if err:
      return err

    data = request.get_json(silent=True) or {}
    floor = FloorService.update_floor(floor, data)
    return success_response(floor.to_dict(), "Floor updated")

  @staticmethod
  def delete_floor(floor_id):
    _, floor, err = get_floor_for_user(floor_id)
    if err:
      return err

    FloorService.delete_floor(floor)
    return success_response(message="Floor deleted")
