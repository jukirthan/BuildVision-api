from flask import Blueprint
from app.middleware import jwt_required_custom
from app.controllers.slab_controller import SlabController

slab_bp = Blueprint("slabs", __name__)


@slab_bp.route("/floor/<int:floor_id>", methods=["GET"])
@jwt_required_custom
def get_slabs(floor_id):
  return SlabController.get_slabs(floor_id)


@slab_bp.route("/<int:slab_id>", methods=["GET"])
@jwt_required_custom
def get_slab(slab_id):
  return SlabController.get_slab(slab_id)


@slab_bp.route("/floor/<int:floor_id>", methods=["POST"])
@jwt_required_custom
def create_slab(floor_id):
  return SlabController.create_slab(floor_id)


@slab_bp.route("/<int:slab_id>", methods=["PUT"])
@jwt_required_custom
def update_slab(slab_id):
  return SlabController.update_slab(slab_id)


@slab_bp.route("/<int:slab_id>", methods=["DELETE"])
@jwt_required_custom
def delete_slab(slab_id):
  return SlabController.delete_slab(slab_id)
