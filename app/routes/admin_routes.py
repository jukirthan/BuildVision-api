from flask import Blueprint
from app.middleware import admin_required
from app.controllers.admin_controller import AdminController

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/overview", methods=["GET"])
@admin_required
def overview():
  """Workspace-wide usage analytics for the admin dashboard."""
  return AdminController.overview()
