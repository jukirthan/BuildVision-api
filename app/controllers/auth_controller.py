from flask import request
from flask_jwt_extended import create_access_token, create_refresh_token
from app.extensions import db
from app.models.user import User
from app.utils import success_response, error_response, validate_required_fields


class AuthController:
  @staticmethod
  def register():
    data = request.get_json() or {}
    error = validate_required_fields(data, ["name", "email", "password"])
    if error:
      return error_response(error, 400)

    if User.query.filter_by(email=data["email"]).first():
      return error_response("Email already registered", 400)

    user = User(
      name=data["name"],
      email=data["email"],
      role=data.get("role", "engineer"),
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()

    return success_response(user.to_dict(), "User registered successfully", 201)

  @staticmethod
  def login():
    data = request.get_json() or {}
    error = validate_required_fields(data, ["email", "password"])
    if error:
      return error_response(error, 400)

    user = User.query.filter_by(email=data["email"]).first()
    if not user or not user.check_password(data["password"]):
      return error_response("Invalid email or password", 401)

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return success_response({
      "user": user.to_dict(),
      "access_token": access_token,
      "refresh_token": refresh_token,
    }, "Login successful")

