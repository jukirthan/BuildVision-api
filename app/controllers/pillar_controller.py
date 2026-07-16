from flask import request
from app.extensions import db
from app.models.pillar import Pillar
from app.models.floor import Floor
from app.models.building import Building
from app.models.project import Project
from app.middleware import get_current_user
from app.services.calculation_service import CalculationService
from app.utils import success_response, error_response, validate_required_fields


class PillarController:
  @staticmethod
  def _check_floor_access(floor_id):
    current = get_current_user()
    floor = Floor.query.get(floor_id)
    if not floor:
      return None, error_response("Floor not found", 404)
    building = Building.query.get(floor.building_id)
    project = Project.query.get(building.project_id)
    if project.user_id != current.id:
      return None, error_response("Forbidden", 403)
    return floor, None

  @staticmethod
  def get_pillars(floor_id):
    _, err = PillarController._check_floor_access(floor_id)
    if err:
      return err
    pillars = Pillar.query.filter_by(floor_id=floor_id).all()
    return success_response([p.to_dict() for p in pillars])

  @staticmethod
  def get_pillar(pillar_id):
    pillar = Pillar.query.get(pillar_id)
    if not pillar:
      return error_response("Pillar not found", 404)
    _, err = PillarController._check_floor_access(pillar.floor_id)
    if err:
      return err
    return success_response(pillar.to_dict())

  @staticmethod
  def create_pillar(floor_id):
    floor, err = PillarController._check_floor_access(floor_id)
    if err:
      return err

    data = request.get_json() or {}
    error = validate_required_fields(data, ["name"])
    if error:
      return error_response(error, 400)

    pillar = Pillar(
      name=data["name"],
      x_position=data.get("x_position", 0.0),
      y_position=data.get("y_position", 0.0),
      width=data.get("width", 0.3),
      depth=data.get("depth", 0.3),
      height=data.get("height", floor.height),
      material=data.get("material", "concrete"),
      floor_id=floor_id,
    )
    pillar.load_capacity = CalculationService.calculate_pillar_load_capacity(
      pillar.width, pillar.depth, pillar.height, pillar.material
    )
    db.session.add(pillar)
    db.session.commit()
    CalculationService.on_pillar_change(pillar)
    return success_response(pillar.to_dict(), "Pillar created", 201)

  @staticmethod
  def move_pillar(pillar_id):
    pillar = Pillar.query.get(pillar_id)
    if not pillar:
      return error_response("Pillar not found", 404)
    _, err = PillarController._check_floor_access(pillar.floor_id)
    if err:
      return err

    data = request.get_json() or {}
    if "x_position" in data:
      pillar.x_position = data["x_position"]
    if "y_position" in data:
      pillar.y_position = data["y_position"]

    db.session.commit()
    CalculationService.on_pillar_change(pillar)
    return success_response(pillar.to_dict(), "Pillar moved")

  @staticmethod
  def resize_pillar(pillar_id):
    pillar = Pillar.query.get(pillar_id)
    if not pillar:
      return error_response("Pillar not found", 404)
    _, err = PillarController._check_floor_access(pillar.floor_id)
    if err:
      return err

    data = request.get_json() or {}
    for field in ["width", "depth", "height"]:
      if field in data:
        setattr(pillar, field, data[field])

    pillar.load_capacity = CalculationService.calculate_pillar_load_capacity(
      pillar.width, pillar.depth, pillar.height, pillar.material
    )
    db.session.commit()
    CalculationService.on_pillar_change(pillar)
    return success_response(pillar.to_dict(), "Pillar resized")

  @staticmethod
  def update_pillar(pillar_id):
    pillar = Pillar.query.get(pillar_id)
    if not pillar:
      return error_response("Pillar not found", 404)
    _, err = PillarController._check_floor_access(pillar.floor_id)
    if err:
      return err

    data = request.get_json() or {}
    for field in ["name", "x_position", "y_position", "width", "depth", "height", "material"]:
      if field in data:
        setattr(pillar, field, data[field])

    pillar.load_capacity = CalculationService.calculate_pillar_load_capacity(
      pillar.width, pillar.depth, pillar.height, pillar.material
    )
    db.session.commit()
    CalculationService.on_pillar_change(pillar)
    return success_response(pillar.to_dict(), "Pillar updated")

  @staticmethod
  def delete_pillar(pillar_id):
    pillar = Pillar.query.get(pillar_id)
    if not pillar:
      return error_response("Pillar not found", 404)
    floor_id = pillar.floor_id
    _, err = PillarController._check_floor_access(floor_id)
    if err:
      return err

    db.session.delete(pillar)
    db.session.commit()
    CalculationService.recalculate_floor_structure(floor_id)
    return success_response(message="Pillar deleted")
