from flask import Blueprint
from app.middleware import jwt_required_custom
from app.controllers.building_controller import BuildingController

building_bp = Blueprint("buildings", __name__)


@building_bp.route("/project/<int:project_id>", methods=["GET"])
@jwt_required_custom
def get_buildings(project_id):
  return BuildingController.get_buildings(project_id)


@building_bp.route("/<int:building_id>", methods=["GET"])
@jwt_required_custom
def get_building(building_id):
  return BuildingController.get_building(building_id)


@building_bp.route("/project/<int:project_id>", methods=["POST"])
@jwt_required_custom
def create_building(project_id):
  return BuildingController.create_building(project_id)


@building_bp.route("/<int:building_id>", methods=["PUT"])
@jwt_required_custom
def update_building(building_id):
  return BuildingController.update_building(building_id)


@building_bp.route("/<int:building_id>", methods=["DELETE"])
@jwt_required_custom
def delete_building(building_id):
  return BuildingController.delete_building(building_id)
