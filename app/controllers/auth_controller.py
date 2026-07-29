from flask import request
from flask_jwt_extended import create_access_token, create_refresh_token
from app.extensions import db
from app.models.user import User
from app.utils import success_response, error_response, validate_required_fields

ALLOWED_ROLES = {"admin", "engineer", "architect", "contractor"}


def _issue_tokens(user):
  # Embed role in the token so admin gates skip a remote user lookup.
  claims = {"role": user.role or "engineer"}
  access_token = create_access_token(
    identity=str(user.id), additional_claims=claims
  )
  refresh_token = create_refresh_token(
    identity=str(user.id), additional_claims=claims
  )
  return {
    "user": user.to_dict(),
    "access_token": access_token,
    "token": access_token,
    "refresh_token": refresh_token,
  }


class AuthController:
  @staticmethod
  def register():
    data = request.get_json(silent=True) or {}
    error = validate_required_fields(data, ["name", "email", "password"])
    if error:
      return error_response(error, 400)

    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    role = str(data.get("role", "engineer")).strip().lower() or "engineer"

    if len(name) < 2:
      return error_response("Name must be at least 2 characters", 400)
    if "@" not in email or "." not in email.split("@")[-1]:
      return error_response("Enter a valid email address", 400)
    if len(password) < 6:
      return error_response("Password must be at least 6 characters", 400)
    if role not in ALLOWED_ROLES:
      return error_response(
        f"Invalid role. Use one of: {', '.join(sorted(ALLOWED_ROLES - {'admin'}))}",
        400,
      )
    # Never allow self-register as admin
    if role == "admin":
      role = "engineer"

    if User.query.filter_by(email=email).first():
      return error_response("Email already registered. Please sign in instead.", 400)

    user = User(name=name, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    # Auto-login after signup so the frontend can redirect immediately
    return success_response(
      _issue_tokens(user),
      "Account created successfully",
      201,
    )

  @staticmethod
  def login():
    data = request.get_json(silent=True) or {}
    error = validate_required_fields(data, ["email", "password"])
    if error:
      return error_response(error, 400)

    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
      return error_response("Invalid email or password", 401)

    return success_response(_issue_tokens(user), "Login successful")
