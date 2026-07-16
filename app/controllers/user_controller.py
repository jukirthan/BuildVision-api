from flask import request
from app.extensions import db
from app.models.user import User
from app.middleware import get_current_user
from app.utils import success_response, error_response, validate_required_fields


class UserController:
  @staticmethod
  def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
      return error_response("User not found", 404)
    return success_response(user.to_dict())

  @staticmethod
  def get_all_users():
    users = User.query.all()
    return success_response([u.to_dict() for u in users])

  @staticmethod
  def create_user():
    data = request.get_json() or {}
    error = validate_required_fields(data, ["name", "email", "password"])
    if error:
      return error_response(error, 400)

    if User.query.filter_by(email=data["email"]).first():
      return error_response("Email already exists", 400)

    user = User(name=data["name"], email=data["email"], role=data.get("role", "engineer"))
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()
    return success_response(user.to_dict(), "User created", 201)

  @staticmethod
  def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
      return error_response("User not found", 404)

    current = get_current_user()
    if current and current.id != user_id and current.role != "admin":
      return error_response("Forbidden", 403)

    data = request.get_json() or {}
    if "name" in data:
      user.name = data["name"]
    if "email" in data:
      user.email = data["email"]
    if "role" in data:
      user.role = data["role"]
    if "password" in data:
      user.set_password(data["password"])

    db.session.commit()
    return success_response(user.to_dict(), "User updated")

  @staticmethod
  def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
      return error_response("User not found", 404)

    current = get_current_user()
    if current and current.id != user_id and current.role != "admin":
      return error_response("Forbidden", 403)

    db.session.delete(user)
    db.session.commit()
    return success_response(message="User deleted")
