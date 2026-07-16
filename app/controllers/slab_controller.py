from flask import request
from app.extensions import db
from app.models.slab import Slab
from app.models.floor import Floor
from app.models.building import Building
from app.models.project import Project
from app.middleware import get_current_user
from app.services.calculation_service import CalculationService
from app.utils import success_response, error_response, validate_required_fields


class SlabController:
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
  def get_slabs(floor_id):
    _, err = SlabController._check_floor_access(floor_id)
    if err:
      return err
    slabs = Slab.query.filter_by(floor_id=floor_id).all()
    return success_response([s.to_dict() for s in slabs])

  @staticmethod
  def get_slab(slab_id):
    slab = Slab.query.get(slab_id)
    if not slab:
      return error_response("Slab not found", 404)
    _, err = SlabController._check_floor_access(slab.floor_id)
    if err:
      return err
    return success_response(slab.to_dict())

  @staticmethod
  def create_slab(floor_id):
    floor, err = SlabController._check_floor_access(floor_id)
    if err:
      return err

    data = request.get_json() or {}
    error = validate_required_fields(data, ["name"])
    if error:
      return error_response(error, 400)

    slab = Slab(
      name=data["name"],
      thickness=data.get("thickness", 0.15),
      area=data.get("area", floor.area),
      material=data.get("material", "concrete"),
      reinforcement=data.get("reinforcement", "standard"),
      floor_id=floor_id,
    )
    slab.load_capacity = CalculationService.calculate_slab_load_capacity(
      slab.thickness, slab.area, slab.material
    )
    db.session.add(slab)
    db.session.commit()
    return success_response(slab.to_dict(), "Slab created", 201)

  @staticmethod
  def update_slab(slab_id):
    slab = Slab.query.get(slab_id)
    if not slab:
      return error_response("Slab not found", 404)
    _, err = SlabController._check_floor_access(slab.floor_id)
    if err:
      return err

    data = request.get_json() or {}
    for field in ["name", "thickness", "area", "material", "reinforcement"]:
      if field in data:
        setattr(slab, field, data[field])

    CalculationService.on_slab_change(slab)
    return success_response(slab.to_dict(), "Slab updated")

  @staticmethod
  def delete_slab(slab_id):
    slab = Slab.query.get(slab_id)
    if not slab:
      return error_response("Slab not found", 404)
    _, err = SlabController._check_floor_access(slab.floor_id)
    if err:
      return err

    db.session.delete(slab)
    db.session.commit()
    return success_response(message="Slab deleted")
