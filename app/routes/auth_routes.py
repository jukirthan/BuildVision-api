from flask import Blueprint
from flask_jwt_extended import jwt_required
from app.controllers.auth_controller import AuthController

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
  return AuthController.refresh()
