from functools import wraps

from flask import g
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request

from app.models.user import User
from app.utils import error_response


def jwt_required_custom(fn):
  @wraps(fn)
  def wrapper(*args, **kwargs):
    try:
      verify_jwt_in_request()
    except Exception:
      return error_response("Unauthorized - invalid or missing token", 401)
    return fn(*args, **kwargs)
  return wrapper


def get_current_user():
  """Load the signed-in user once per request (avoids repeat remote DB hits)."""
  if "current_user" in g:
    return g.current_user

  user_id = get_jwt_identity()
  if not user_id:
    g.current_user = None
    return None

  user = User.query.get(int(user_id))
  g.current_user = user
  return user


def is_admin(user=None):
  if user is not None:
    return getattr(user, "role", None) == "admin"
  # Prefer JWT claim — no DB round-trip on the hot admin path.
  try:
    role = (get_jwt() or {}).get("role")
    if role is not None:
      return str(role).lower() == "admin"
  except Exception:
    pass
  db_user = get_current_user()
  return bool(db_user) and getattr(db_user, "role", None) == "admin"


def admin_required(fn):
  """Verifies a valid token *and* that the caller is an administrator.

  Role is read from the JWT claim when present so admin pages do not pay an
  extra remote DB lookup (~400ms on Railway) just to check permissions.
  """
  @wraps(fn)
  def wrapper(*args, **kwargs):
    try:
      verify_jwt_in_request()
    except Exception:
      return error_response("Unauthorized - invalid or missing token", 401)
    if not is_admin():
      return error_response("Forbidden - administrator access required", 403)
    return fn(*args, **kwargs)
  return wrapper


def log_request(fn):
  @wraps(fn)
  def wrapper(*args, **kwargs):
    return fn(*args, **kwargs)
  return wrapper
