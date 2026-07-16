from flask import Blueprint
from app.middleware import jwt_required_custom
from app.controllers.user_controller import UserController

user_bp = Blueprint("users", __name__)


@user_bp.route("/", methods=["GET"])
@jwt_required_custom
def get_all_users():
  return UserController.get_all_users()


@user_bp.route("/<int:user_id>", methods=["GET"])
@jwt_required_custom
def get_user(user_id):
  return UserController.get_user(user_id)


@user_bp.route("/", methods=["POST"])
@jwt_required_custom
def create_user():
  return UserController.create_user()


@user_bp.route("/<int:user_id>", methods=["PUT"])
@jwt_required_custom
def update_user(user_id):
  return UserController.update_user(user_id)


@user_bp.route("/<int:user_id>", methods=["DELETE"])
@jwt_required_custom
def delete_user(user_id):
  return UserController.delete_user(user_id)
