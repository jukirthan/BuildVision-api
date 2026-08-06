from flask import request
from flask_jwt_extended import (
  create_access_token,
  create_refresh_token,
  get_jwt,
  get_jwt_identity,
)
from app.extensions import db
from app.models.user import User
from app.security.passwords import validate_password_strength
from app.utils import success_response, error_response, validate_required_fields

ALLOWED_ROLES = {"admin", "engineer", "architect", "contractor"}


def _issue_tokens(user):
  # Embed role in the token so admin gates skip a remote user lookup.
  claims = {"role": (user.role or "engineer").lower()}
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
    strength_error = validate_password_strength(password)
    if strength_error:
      return error_response(strength_error, 400)
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

  @staticmethod
  def refresh():
    """Rotate access token while preserving role claims from the refresh JWT."""
    user_id = get_jwt_identity()
    claims = get_jwt() or {}
    role = str(claims.get("role") or "engineer").lower()

    # Prefer live role from DB when reachable so demotions take effect.
    user = User.query.get(int(user_id)) if user_id else None
    if user:
      role = (user.role or role).lower()

    access_token = create_access_token(
      identity=str(user_id),
      additional_claims={"role": role},
    )
    return success_response(
      {
        "access_token": access_token,
        "token": access_token,
        "role": role,
      },
      "Token refreshed",
    )
