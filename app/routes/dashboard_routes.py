from flask import Blueprint
from app.middleware import jwt_required_custom
from app.controllers.dashboard_controller import DashboardController

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/summary", methods=["GET"])
@jwt_required_custom
def project_summary():
  return DashboardController.project_summary()


@dashboard_bp.route("/building/<int:building_id>/statistics", methods=["GET"])
@jwt_required_custom
def building_statistics(building_id):
  return DashboardController.building_statistics(building_id)


@dashboard_bp.route("/floor/<int:floor_id>/materials", methods=["GET"])
@jwt_required_custom
def material_information(floor_id):
  return DashboardController.material_information(floor_id)
