from flask import Blueprint
from app.middleware import jwt_required_custom
from app.controllers.project_controller import ProjectController

project_bp = Blueprint("projects", __name__)


@project_bp.route("/", methods=["GET"])
@jwt_required_custom
def get_projects():
  return ProjectController.get_projects()


@project_bp.route("/<int:project_id>", methods=["GET"])
@jwt_required_custom
def get_project(project_id):
  return ProjectController.get_project(project_id)


@project_bp.route("/", methods=["POST"])
@jwt_required_custom
def create_project():
  return ProjectController.create_project()


@project_bp.route("/<int:project_id>", methods=["PUT"])
@jwt_required_custom
def update_project(project_id):
  return ProjectController.update_project(project_id)


@project_bp.route("/<int:project_id>", methods=["DELETE"])
@jwt_required_custom
def delete_project(project_id):
  return ProjectController.delete_project(project_id)
