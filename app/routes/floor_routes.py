from flask import Blueprint
from app.middleware import jwt_required_custom
from app.controllers.floor_controller import FloorController

floor_bp = Blueprint("floors", __name__)


@floor_bp.route("/building/<int:building_id>", methods=["GET"])
@jwt_required_custom
def get_floors(building_id):
  return FloorController.get_floors(building_id)


@floor_bp.route("/<int:floor_id>", methods=["GET"])
@jwt_required_custom
def get_floor(floor_id):
  return FloorController.get_floor(floor_id)


@floor_bp.route("/building/<int:building_id>", methods=["POST"])
@jwt_required_custom
def create_floor(building_id):
  return FloorController.create_floor(building_id)


@floor_bp.route("/<int:floor_id>", methods=["PUT"])
@jwt_required_custom
def update_floor(floor_id):
  return FloorController.update_floor(floor_id)


@floor_bp.route("/<int:floor_id>", methods=["DELETE"])
@jwt_required_custom
def delete_floor(floor_id):
  return FloorController.delete_floor(floor_id)
