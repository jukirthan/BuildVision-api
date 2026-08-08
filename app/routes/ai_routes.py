from flask import Blueprint

from app.controllers.ai_controller import AiController
from app.middleware import jwt_required_custom


ai_bp = Blueprint("ai", __name__)


@ai_bp.route("/chat", methods=["POST"])
@jwt_required_custom
def chat():
  return AiController.chat()
