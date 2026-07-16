from functools import wraps
from flask import request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
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
  user_id = get_jwt_identity()
  if not user_id:
    return None
  return User.query.get(int(user_id))


def log_request(fn):
  @wraps(fn)
  def wrapper(*args, **kwargs):
    return fn(*args, **kwargs)
  return wrapper
