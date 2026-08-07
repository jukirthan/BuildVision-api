from flask import request
from app.access import get_project_for_user, get_building_for_user
from app.services.building_service import BuildingService
from app.utils import success_response, error_response, validate_required_fields
from app.extensions import db


class BuildingController:
  @staticmethod
  def get_design(building_id):
    _, building, err = get_building_for_user(building_id)
    if err:
      return err
    return success_response({
      "snapshot": building.design_snapshot,
      "version": building.design_version or 0,
    })

  @staticmethod
  def put_design(building_id):
    _, building, err = get_building_for_user(building_id, write=True)
    if err:
      return err
    data = request.get_json(silent=True) or {}
    snapshot = data.get("snapshot")
    version = data.get("version")
    if not isinstance(snapshot, dict) or not isinstance(version, int):
      return error_response("snapshot must be an object and version must be an integer", 400)
    current = building.design_version or 0
    if version != current:
      return error_response(
        f"Design has changed on the server (current version: {current})", 409
      )
    building.design_snapshot = snapshot
    building.design_version = current + 1
    db.session.commit()
    return success_response({
      "snapshot": building.design_snapshot,
      "version": building.design_version,
    }, "Design saved")

  @staticmethod
  def get_buildings(project_id):
    _, _, err = get_project_for_user(project_id)
    if err:
      return err
    buildings = BuildingService.get_buildings_by_project(project_id)
    return success_response([b.to_dict() for b in buildings])

  @staticmethod
  def get_building(building_id):
    _, building, err = get_building_for_user(building_id)
    if err:
      return err
    return success_response(building.to_dict(include_floors=True))

  @staticmethod
  def create_building(project_id):
    _, _, err = get_project_for_user(project_id, write=True)
    if err:
      return err

    data = request.get_json(silent=True) or {}
    error = validate_required_fields(data, ["name"])
    if error:
      return error_response(error, 400)

    building, err_msg = BuildingService.create_building(data, project_id)
    if err_msg:
      return error_response(err_msg, 404)
    return success_response(building.to_dict(include_floors=True), "Building created", 201)

  @staticmethod
  def update_building(building_id):
    _, building, err = get_building_for_user(building_id, write=True)
    if err:
      return err

    data = request.get_json(silent=True) or {}
    building = BuildingService.update_building(building, data)
    return success_response(building.to_dict(), "Building updated")

  @staticmethod
  def delete_building(building_id):
    _, building, err = get_building_for_user(building_id, write=True)
    if err:
      return err

    BuildingService.delete_building(building)
    return success_response(message="Building deleted")
