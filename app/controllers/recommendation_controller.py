from flask import request
from app.access import get_floor_for_user, current_user_or_401
from app.models.building import Building
from app.services.recommendation_service import suggest_layouts
from app.utils import success_response, error_response


class RecommendationController:
  @staticmethod
  def suggest_for_floor(floor_id):
    _, floor, err = get_floor_for_user(floor_id)
    if err:
      return err
    building = Building.query.get(floor.building_id)
    if not building:
      return error_response("Building not found", 404)

    suggestions = suggest_layouts(
      width=building.width or 30,
      length=building.length or 20,
      floors=building.total_floors or 1,
      floor_height=floor.height or 3.5,
    )
    return success_response({"suggestions": suggestions})

  @staticmethod
  def suggest_from_body():
    user, err = current_user_or_401()
    if err:
      return err
    # contractor is read-only for POST layouts per docs
    if getattr(user, "role", None) == "contractor":
      return error_response("Contractors can view suggestions but not generate new layouts", 403)

    data = request.get_json(silent=True) or {}
    width = data.get("width", 30)
    length = data.get("length", 20)
    floors = data.get("floors", 3)
    floor_height = data.get("floor_height", 3.5)
    suggestions = suggest_layouts(width, length, floors, floor_height)
    return success_response({"suggestions": suggestions})
