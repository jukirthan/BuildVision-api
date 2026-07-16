from flask import Blueprint
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from app.controllers.auth_controller import AuthController
from app.utils import success_response

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
  return AuthController.register()


@auth_bp.route("/login", methods=["POST"])
def login():
  return AuthController.login()


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
  user_id = get_jwt_identity()
  access_token = create_access_token(identity=user_id)
  return success_response({"access_token": access_token}, "Token refreshed")
