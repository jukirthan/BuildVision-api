from flask import request
from app.extensions import db
from app.models.beam import Beam
from app.models.floor import Floor
from app.models.building import Building
from app.models.project import Project
from app.middleware import get_current_user
from app.services.calculation_service import CalculationService
from app.utils import success_response, error_response, validate_required_fields


class BeamController:
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
  def get_beams(floor_id):
    _, err = BeamController._check_floor_access(floor_id)
    if err:
      return err
    beams = Beam.query.filter_by(floor_id=floor_id).all()
    return success_response([b.to_dict() for b in beams])

  @staticmethod
  def get_beam(beam_id):
    beam = Beam.query.get(beam_id)
    if not beam:
      return error_response("Beam not found", 404)
    _, err = BeamController._check_floor_access(beam.floor_id)
    if err:
      return err
    return success_response(beam.to_dict())

  @staticmethod
  def create_beam(floor_id):
    _, err = BeamController._check_floor_access(floor_id)
    if err:
      return err

    data = request.get_json() or {}
    error = validate_required_fields(data, ["name"])
    if error:
      return error_response(error, 400)

    beam = Beam(
      name=data["name"],
      start_x=data.get("start_x", 0.0),
      start_y=data.get("start_y", 0.0),
      end_x=data.get("end_x", 0.0),
      end_y=data.get("end_y", 0.0),
      width=data.get("width", 0.25),
      depth=data.get("depth", 0.4),
      material=data.get("material", "concrete"),
      floor_id=floor_id,
    )
    beam.length = CalculationService.calculate_beam_length(
      beam.start_x, beam.start_y, beam.end_x, beam.end_y
    )
    beam.load_bearing = CalculationService.calculate_beam_load_bearing(
      beam.width, beam.depth, beam.length, beam.material
    )
    db.session.add(beam)
    db.session.commit()
    CalculationService.on_beam_change(beam)
    return success_response(beam.to_dict(), "Beam created", 201)

  @staticmethod
  def update_beam(beam_id):
    beam = Beam.query.get(beam_id)
    if not beam:
      return error_response("Beam not found", 404)
    _, err = BeamController._check_floor_access(beam.floor_id)
    if err:
      return err

    data = request.get_json() or {}
    for field in ["name", "start_x", "start_y", "end_x", "end_y", "width", "depth", "material"]:
      if field in data:
        setattr(beam, field, data[field])

    beam.length = CalculationService.calculate_beam_length(
      beam.start_x, beam.start_y, beam.end_x, beam.end_y
    )
    beam.load_bearing = CalculationService.calculate_beam_load_bearing(
      beam.width, beam.depth, beam.length, beam.material
    )
    db.session.commit()
    CalculationService.on_beam_change(beam)
    return success_response(beam.to_dict(), "Beam updated")

  @staticmethod
  def delete_beam(beam_id):
    beam = Beam.query.get(beam_id)
    if not beam:
      return error_response("Beam not found", 404)
    floor_id = beam.floor_id
    _, err = BeamController._check_floor_access(floor_id)
    if err:
      return err

    db.session.delete(beam)
    db.session.commit()
    CalculationService.recalculate_slabs_for_floor(floor_id)
    db.session.commit()
    return success_response(message="Beam deleted")
