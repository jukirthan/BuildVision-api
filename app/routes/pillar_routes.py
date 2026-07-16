from flask import Blueprint
from app.middleware import jwt_required_custom
from app.controllers.pillar_controller import PillarController

pillar_bp = Blueprint("pillars", __name__)


@pillar_bp.route("/floor/<int:floor_id>", methods=["GET"])
@jwt_required_custom
def get_pillars(floor_id):
  return PillarController.get_pillars(floor_id)


@pillar_bp.route("/<int:pillar_id>", methods=["GET"])
@jwt_required_custom
def get_pillar(pillar_id):
  return PillarController.get_pillar(pillar_id)


@pillar_bp.route("/floor/<int:floor_id>", methods=["POST"])
@jwt_required_custom
def create_pillar(floor_id):
  return PillarController.create_pillar(floor_id)


@pillar_bp.route("/<int:pillar_id>", methods=["PUT"])
@jwt_required_custom
def update_pillar(pillar_id):
  return PillarController.update_pillar(pillar_id)


@pillar_bp.route("/<int:pillar_id>/move", methods=["PUT"])
@jwt_required_custom
def move_pillar(pillar_id):
  return PillarController.move_pillar(pillar_id)


@pillar_bp.route("/<int:pillar_id>/resize", methods=["PUT"])
@jwt_required_custom
def resize_pillar(pillar_id):
  return PillarController.resize_pillar(pillar_id)


@pillar_bp.route("/<int:pillar_id>", methods=["DELETE"])
@jwt_required_custom
def delete_pillar(pillar_id):
  return PillarController.delete_pillar(pillar_id)
