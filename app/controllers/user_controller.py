from flask import request
from sqlalchemy import func
from app.extensions import db
from app.models.user import User
from app.models.project import Project
from app.middleware import get_current_user, is_admin
from app.utils import success_response, error_response, validate_required_fields

# Kept in sync with ALLOWED_ROLES in auth_controller (plus "viewer", which is
# assignable by an admin but not self-selectable at signup).
VALID_ROLES = ("admin", "engineer", "architect", "contractor", "viewer")


def _admin_count(exclude_id=None):
  query = User.query.filter_by(role="admin")
  if exclude_id is not None:
    query = query.filter(User.id != exclude_id)
  return query.count()


class UserController:
  @staticmethod
  def get_user(user_id):
    current = get_current_user()
    # A regular account may only read itself; admins may read anyone.
    if current and current.id != user_id and not is_admin(current):
      return error_response("Forbidden", 403)

    user = User.query.get(user_id)
    if not user:
      return error_response("User not found", 404)
    return success_response(user.to_dict())

  @staticmethod
  def get_all_users():
    """Admin user directory with optional search / role filter.

    Includes each user's project count so the admin table can show real
    activity without an N+1 round trip per row.
    """
    search = (request.args.get("search") or "").strip().lower()
    role = (request.args.get("role") or "").strip().lower()

    query = User.query
    if search:
      like = f"%{search}%"
      query = query.filter(
        db.or_(func.lower(User.name).like(like), func.lower(User.email).like(like))
      )
    if role and role != "all":
      query = query.filter(func.lower(User.role) == role)

    users = query.order_by(User.id.desc()).all()

    # One grouped query for all project counts.
    counts = dict(
      db.session.query(Project.user_id, func.count(Project.id))
      .group_by(Project.user_id)
      .all()
    )

    payload = []
    for u in users:
      row = u.to_dict()
      row["project_count"] = int(counts.get(u.id, 0))
      payload.append(row)

    return success_response(payload)

  @staticmethod
  def create_user():
    data = request.get_json() or {}
    error = validate_required_fields(data, ["name", "email", "password"])
    if error:
      return error_response(error, 400)

    email = (data["email"] or "").strip().lower()
    if User.query.filter(func.lower(User.email) == email).first():
      return error_response("Email already exists", 400)

    role = (data.get("role") or "engineer").strip().lower()
    if role not in VALID_ROLES:
      return error_response(
        f"Invalid role. Expected one of: {', '.join(VALID_ROLES)}", 400
      )

    user = User(name=data["name"].strip(), email=email, role=role)
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
    if current and current.id != user_id and not is_admin(current):
      return error_response("Forbidden", 403)

    data = request.get_json() or {}

    if "name" in data and data["name"]:
      user.name = data["name"].strip()

    if "email" in data and data["email"]:
      email = data["email"].strip().lower()
      clash = User.query.filter(
        func.lower(User.email) == email, User.id != user.id
      ).first()
      if clash:
        return error_response("Email already in use", 400)
      user.email = email

    if "role" in data and data["role"]:
      # Only an admin may change roles at all.
      if not is_admin(current):
        return error_response("Forbidden - only an admin can change roles", 403)
      role = data["role"].strip().lower()
      if role not in VALID_ROLES:
        return error_response(
          f"Invalid role. Expected one of: {', '.join(VALID_ROLES)}", 400
        )
      # Never allow the workspace to end up with zero admins.
      if user.role == "admin" and role != "admin" and _admin_count(exclude_id=user.id) == 0:
        return error_response(
          "Cannot change role: at least one administrator is required", 400
        )
      user.role = role

    if "password" in data and data["password"]:
      user.set_password(data["password"])

    db.session.commit()
    return success_response(user.to_dict(), "User updated")

  @staticmethod
  def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
      return error_response("User not found", 404)

    current = get_current_user()
    if current and current.id != user_id and not is_admin(current):
      return error_response("Forbidden", 403)

    # Guard rails against locking everybody out of the workspace.
    if current and current.id == user_id and is_admin(current):
      return error_response("You cannot delete your own admin account", 400)
    if user.role == "admin" and _admin_count(exclude_id=user.id) == 0:
      return error_response(
        "Cannot delete the last administrator account", 400
      )

    db.session.delete(user)
    db.session.commit()
    return success_response(message="User deleted")
