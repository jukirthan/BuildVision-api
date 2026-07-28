from flask import Blueprint
from app.middleware import jwt_required_custom, admin_required, get_current_user
from app.controllers.auth_controller import AuthController
from app.controllers.user_controller import UserController
from app.utils import success_response, error_response

user_bp = Blueprint("users", __name__)


# Aliases matching frontend + API docs (/api/users/*)
@user_bp.route("/register", methods=["POST"])
def register():
  return AuthController.register()


@user_bp.route("/login", methods=["POST"])
def login():
  return AuthController.login()


@user_bp.route("/profile", methods=["GET"])
@jwt_required_custom
def get_profile():
  user = get_current_user()
  if not user:
    return error_response("Unauthorized", 401)
  return success_response(user.to_dict())


@user_bp.route("/profile", methods=["PUT"])
@jwt_required_custom
def update_profile():
  user = get_current_user()
  if not user:
    return error_response("Unauthorized", 401)
  return UserController.update_user(user.id)


# ── Administrator-only user directory ─────────────────────────────────
# These expose or mutate *other* people's accounts, so they are gated on
# role rather than merely on a valid token.
@user_bp.route("/", methods=["GET"])
@admin_required
def get_all_users():
  return UserController.get_all_users()


@user_bp.route("/<int:user_id>", methods=["GET"])
@jwt_required_custom
def get_user(user_id):
  return UserController.get_user(user_id)


@user_bp.route("/", methods=["POST"])
@admin_required
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
