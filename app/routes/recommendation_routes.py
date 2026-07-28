from flask import Blueprint
from app.middleware import jwt_required_custom
from app.controllers.recommendation_controller import RecommendationController

recommendation_bp = Blueprint("recommendations", __name__)


@recommendation_bp.route("/floor/<int:floor_id>", methods=["GET"])
@jwt_required_custom
def suggest_for_floor(floor_id):
  return RecommendationController.suggest_for_floor(floor_id)


@recommendation_bp.route("/layouts", methods=["POST"])
@jwt_required_custom
def suggest_layouts():
  return RecommendationController.suggest_from_body()
