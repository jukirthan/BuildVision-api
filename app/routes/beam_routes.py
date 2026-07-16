from flask import Blueprint
from app.middleware import jwt_required_custom
from app.controllers.beam_controller import BeamController

beam_bp = Blueprint("beams", __name__)


@beam_bp.route("/floor/<int:floor_id>", methods=["GET"])
@jwt_required_custom
def get_beams(floor_id):
  return BeamController.get_beams(floor_id)


@beam_bp.route("/<int:beam_id>", methods=["GET"])
@jwt_required_custom
def get_beam(beam_id):
  return BeamController.get_beam(beam_id)


@beam_bp.route("/floor/<int:floor_id>", methods=["POST"])
@jwt_required_custom
def create_beam(floor_id):
  return BeamController.create_beam(floor_id)


@beam_bp.route("/<int:beam_id>", methods=["PUT"])
@jwt_required_custom
def update_beam(beam_id):
  return BeamController.update_beam(beam_id)


@beam_bp.route("/<int:beam_id>", methods=["DELETE"])
@jwt_required_custom
def delete_beam(beam_id):
  return BeamController.delete_beam(beam_id)
