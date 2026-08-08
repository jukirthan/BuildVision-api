"""Transactional load/save for the complete floor-owned building model."""

import math
from uuid import uuid4

from app.dto import camel_to_snake, snake_to_camel
from app.extensions import db
from app.models.beam import Beam
from app.models.building import Building
from app.models.floor import Floor
from app.models.pillar import Pillar
from app.models.slab import Slab
from app.services.calculation_service import CalculationService


class StructureValidationError(ValueError):
  def __init__(self, message, errors=None):
    super().__init__(message)
    self.errors = errors or []


def _positive(value, name, minimum, maximum):
  try:
    number = float(value)
  except (TypeError, ValueError) as exc:
    raise StructureValidationError(f"{name} must be a number") from exc
  if number < minimum or number > maximum:
    raise StructureValidationError(
      f"{name} must be between {minimum:g} and {maximum:g}"
    )
  return number


def _within(value, name, minimum, maximum):
  try:
    number = float(value)
  except (TypeError, ValueError) as exc:
    raise StructureValidationError(f"{name} must be a number") from exc
  if number < minimum - 1e-6 or number > maximum + 1e-6:
    raise StructureValidationError(f"{name} must be inside the building footprint")
  return number


def _reference(raw, *keys):
  for key in keys:
    if raw.get(key) not in (None, ""):
      return str(raw[key])
  return None


def _find_existing(model, raw, floor_id):
  client_id = _reference(raw, "client_id", "id")
  if client_id:
    found = model.query.filter_by(client_id=client_id, floor_id=floor_id).first()
    if found:
      return found
  raw_id = raw.get("id")
  if isinstance(raw_id, int):
    found = model.query.filter_by(id=raw_id, floor_id=floor_id).first()
    if found:
      return found
  return None


def _set_common(obj, raw):
  obj.client_id = _reference(raw, "client_id", "id") or str(uuid4())
  if "name" in raw:
    obj.name = str(raw["name"]).strip() or obj.name


def _canonical_floor_payload(floor):
  pillars = list(floor.pillars)
  pillar_ids = {pillar.id: pillar.client_id for pillar in pillars}
  return {
    "id": floor.client_id,
    "floorNumber": floor.floor_number,
    "name": floor.name,
    "elevation": floor.elevation,
    "height": floor.height,
    "pillars": [{
      "id": pillar.client_id,
      "floorId": floor.client_id,
      "stackId": pillar.stack_id,
      "name": pillar.name,
      "x": pillar.x_position,
      "y": pillar.y_position,
      "width": pillar.width,
      "depth": pillar.depth,
      "height": pillar.height,
      "baseElevation": pillar.base_elevation,
      "material": pillar.material,
      "concreteGrade": pillar.concrete_grade,
      "steelGrade": pillar.steel_grade,
      "reinforcement": pillar.reinforcement,
      "loads": pillar.loads,
      "check": pillar.check_result,
      "clearCoverMm": pillar.clear_cover_mm,
      "shape": pillar.shape,
      "rotationDeg": pillar.rotation_deg,
      "loadCapacity": pillar.load_capacity,
    } for pillar in pillars],
    "beams": [{
      "id": beam.client_id,
      "floorId": floor.client_id,
      "name": beam.name,
      "startPillarId": pillar_ids.get(beam.start_pillar_id, ""),
      "endPillarId": pillar_ids.get(beam.end_pillar_id, ""),
      "start": {"x": beam.start_x, "y": beam.start_y},
      "end": {"x": beam.end_x, "y": beam.end_y},
      "startX": beam.start_x,
      "startY": beam.start_y,
      "endX": beam.end_x,
      "endY": beam.end_y,
      "width": beam.width,
      "depth": beam.depth,
      "height": beam.depth,
      "length": beam.length,
      "material": beam.material,
      "loadBearing": beam.load_bearing,
      "concreteGrade": beam.concrete_grade,
      "steelGrade": beam.steel_grade,
      "reinforcement": beam.reinforcement,
      "supportCondition": beam.support_condition,
      "loads": beam.loads,
      "check": beam.check_result,
    } for beam in floor.beams],
    "slabs": [{
      "id": slab.client_id,
      "floorId": floor.client_id,
      "name": slab.name,
      "thickness": slab.thickness,
      "area": slab.area,
      "width": math.sqrt(max(slab.area, 0.01)),
      "length": math.sqrt(max(slab.area, 0.01)),
      "centerX": 0,
      "centerY": 0,
      "material": slab.material,
      "system": slab.system,
      "reinforcement": slab.reinforcement,
      "reinforcementData": slab.reinforcement_data,
      "loads": slab.loads,
      "check": slab.check_result,
      "loadCapacity": slab.load_capacity,
    } for slab in floor.slabs],
    "walls": [],
    "openings": [],
    "stairs": [],
    "structuralWarningCount": 0,
  }


def _structure_payload(building):
  floors = sorted(building.floors, key=lambda floor: floor.floor_number)
  payload = {
    "building": building.to_dict(include_floors=False),
    "floors": [_canonical_floor_payload(floor) for floor in floors],
    "version": building.design_version or 0,
    "cost": CalculationService.estimate_building_materials(building),
  }
  if isinstance(building.design_snapshot, dict):
    payload["snapshot"] = building.design_snapshot
  return snake_to_camel(payload)


class StructureSyncService:
  @staticmethod
  def load(building):
    return _structure_payload(building)

  @staticmethod
  def save(building, payload, expected_version):
    if not isinstance(payload, dict):
      raise StructureValidationError("Structure payload must be an object")
    data = camel_to_snake(payload)
    floors_data = data.get("floors")
    if not isinstance(floors_data, list) or not floors_data:
      raise StructureValidationError("floors must be a non-empty array")
    if len(floors_data) > 50:
      raise StructureValidationError("A building may contain at most 50 floors")
    current_version = building.design_version or 0
    if expected_version != current_version:
      raise StructureValidationError(
        f"Design has changed on the server (current version: {current_version})"
      )

    floor_numbers = [item.get("floor_number") for item in floors_data]
    if any(not isinstance(number, int) or number < 1 for number in floor_numbers):
      raise StructureValidationError("floor_number must be a positive integer")
    if len(set(floor_numbers)) != len(floor_numbers):
      raise StructureValidationError("Floor numbers must be unique within a building")
    floor_ids = [_reference(item, "client_id", "id") for item in floors_data]
    if len([item for item in floor_ids if item]) != len(set(item for item in floor_ids if item)):
      raise StructureValidationError("Floor client IDs must be unique within a building")

    existing_floors = {floor.client_id: floor for floor in building.floors if floor.client_id}
    existing_by_id = {str(floor.id): floor for floor in building.floors}
    seen_floor_ids = set()
    floor_rows = []

    for raw_floor in sorted(floors_data, key=lambda item: item["floor_number"]):
      ref = _reference(raw_floor, "client_id", "id")
      floor = existing_floors.get(ref) or existing_by_id.get(ref)
      if floor is None:
        floor = Floor(client_id=ref or str(uuid4()), building_id=building.id)
        db.session.add(floor)
      _set_common(floor, raw_floor)
      floor.floor_number = raw_floor["floor_number"]
      floor.name = str(raw_floor.get("name") or f"Floor {floor.floor_number}")
      default_floor_height = (building.height / max(len(floors_data), 1)) if building.height else 3.0
      floor.height = _positive(raw_floor.get("height", default_floor_height), "floor height", 1.5, 20)
      floor.elevation = float(raw_floor.get("elevation", 0.0) or 0.0)
      floor.area = float(raw_floor.get("area", (building.width or 0) * (building.length or 0)) or 0)
      floor.building_id = building.id
      seen_floor_ids.add(floor.client_id)
      floor_rows.append((floor, raw_floor))

    for floor in list(building.floors):
      if floor.client_id not in seen_floor_ids:
        db.session.delete(floor)
    db.session.flush()

    for floor, raw_floor in floor_rows:
      StructureSyncService._save_floor_members(building, floor, raw_floor)

    building.total_floors = len(floor_rows)
    building.height = sum(floor.height for floor, _ in floor_rows)
    building.design_version = current_version + 1
    # Keep ancillary planner entities (walls, openings, stairs, foundation,
    # roof and reports) in the same revision while normalized structural
    # members are persisted in their relational tables above.
    building.design_snapshot = payload
    db.session.flush()
    return _structure_payload(building)

  @staticmethod
  def _save_floor_members(building, floor, raw_floor):
    raw_pillars = raw_floor.get("pillars", [])
    raw_beams = raw_floor.get("beams", [])
    raw_slabs = raw_floor.get("slabs", [])
    if not all(isinstance(items, list) for items in (raw_pillars, raw_beams, raw_slabs)):
      raise StructureValidationError("pillars, beams and slabs must be arrays")
    for label, items in (("pillar", raw_pillars), ("beam", raw_beams), ("slab", raw_slabs)):
      refs = [_reference(item, "client_id", "id") for item in items]
      refs = [ref for ref in refs if ref]
      if len(refs) != len(set(refs)):
        raise StructureValidationError(f"{label} client IDs must be unique within a floor")

    pillar_refs = {}
    seen_pillars = set()
    for raw in raw_pillars:
      pillar = _find_existing(Pillar, raw, floor.id) or Pillar(floor_id=floor.id)
      _set_common(pillar, raw)
      pillar.name = str(raw.get("name") or pillar.name or f"P{len(seen_pillars) + 1}")
      pillar.x_position = _within(raw.get("x", raw.get("x_position", 0)), "pillar x", 0, building.width)
      pillar.y_position = _within(raw.get("y", raw.get("y_position", 0)), "pillar y", 0, building.length)
      pillar.width = _positive(raw.get("width", 0.3), "pillar width", 0.05, 10)
      pillar.depth = _positive(raw.get("depth", 0.3), "pillar depth", 0.05, 10)
      pillar.height = _positive(raw.get("height", floor.height), "pillar height", 0.5, 20)
      pillar.base_elevation = float(raw.get("base_elevation", floor.elevation) or floor.elevation)
      pillar.material = str(raw.get("material", "concrete"))
      pillar.stack_id = str(raw.get("stack_id") or f"stack-{pillar.x_position:.3f}-{pillar.y_position:.3f}")
      pillar.concrete_grade = raw.get("concrete_grade", pillar.concrete_grade or "M25")
      pillar.steel_grade = raw.get("steel_grade", pillar.steel_grade or "Fe500")
      pillar.clear_cover_mm = float(raw.get("clear_cover_mm", pillar.clear_cover_mm or 40))
      pillar.shape = raw.get("shape", pillar.shape or "square")
      pillar.rotation_deg = float(raw.get("rotation_deg", pillar.rotation_deg or 0))
      pillar.reinforcement = raw.get("reinforcement", raw.get("longitudinal_bars"))
      pillar.loads = raw.get("loads")
      pillar.check_result = raw.get("check", raw.get("check_result"))
      pillar.load_capacity = CalculationService.calculate_pillar_load_capacity(
        pillar.width, pillar.depth, pillar.height, pillar.material
      )
      pillar.floor_id = floor.id
      db.session.add(pillar)
      ref = _reference(raw, "client_id", "id") or pillar.client_id
      pillar_refs[ref] = pillar
      pillar_refs[pillar.client_id] = pillar
      seen_pillars.add(pillar.client_id)

    for pillar in list(floor.pillars):
      if pillar.client_id not in seen_pillars:
        db.session.delete(pillar)
    db.session.flush()

    seen_beams = set()
    for raw in raw_beams:
      beam = _find_existing(Beam, raw, floor.id) or Beam(floor_id=floor.id)
      _set_common(beam, raw)
      beam.name = str(raw.get("name") or beam.name or f"B{len(seen_beams) + 1}")
      start_ref = _reference(raw, "start_pillar_id", "startPillarId")
      end_ref = _reference(raw, "end_pillar_id", "endPillarId")
      start = pillar_refs.get(start_ref)
      end = pillar_refs.get(end_ref)
      if not start or not end:
        raise StructureValidationError("Beam endpoints must reference pillars on the same floor")
      if start.floor_id != floor.id or end.floor_id != floor.id:
        raise StructureValidationError("Beam endpoints must belong to the beam floor")
      beam.start_pillar_id = start.id
      beam.end_pillar_id = end.id
      beam.start_x = _within(raw.get("start_x", raw.get("startX", start.x_position)), "beam start x", 0, building.width)
      beam.start_y = _within(raw.get("start_y", raw.get("startY", start.y_position)), "beam start y", 0, building.length)
      beam.end_x = _within(raw.get("end_x", raw.get("endX", end.x_position)), "beam end x", 0, building.width)
      beam.end_y = _within(raw.get("end_y", raw.get("endY", end.y_position)), "beam end y", 0, building.length)
      beam.width = _positive(raw.get("width", 0.25), "beam width", 0.05, 5)
      beam.depth = _positive(raw.get("depth", 0.4), "beam depth", 0.05, 10)
      beam.material = str(raw.get("material", "concrete"))
      beam.length = CalculationService.calculate_beam_length(beam.start_x, beam.start_y, beam.end_x, beam.end_y)
      if beam.length <= 0:
        raise StructureValidationError("Beam endpoints must not be coincident")
      beam.load_bearing = CalculationService.calculate_beam_load_bearing(beam.width, beam.depth, beam.length, beam.material)
      beam.concrete_grade = raw.get("concrete_grade", beam.concrete_grade or "M25")
      beam.steel_grade = raw.get("steel_grade", beam.steel_grade or "Fe500")
      beam.reinforcement = raw.get("reinforcement")
      beam.support_condition = raw.get("support_condition", beam.support_condition or "continuous")
      beam.loads = raw.get("loads")
      beam.check_result = raw.get("check", raw.get("check_result"))
      beam.floor_id = floor.id
      db.session.add(beam)
      seen_beams.add(beam.client_id)

    for beam in list(floor.beams):
      if beam.client_id not in seen_beams:
        db.session.delete(beam)
    db.session.flush()

    seen_slabs = set()
    for raw in raw_slabs:
      slab = _find_existing(Slab, raw, floor.id) or Slab(floor_id=floor.id)
      _set_common(slab, raw)
      slab.name = str(raw.get("name") or slab.name or f"S{len(seen_slabs) + 1}")
      slab.thickness = _positive(raw.get("thickness", 0.15), "slab thickness", 0.05, 1.5)
      slab.area = _positive(raw.get("area", floor.area), "slab area", 0.01, max((building.width or 1) * (building.length or 1) * 1.5, 1))
      slab.material = str(raw.get("material", "concrete"))
      slab.reinforcement = str(raw.get("reinforcement", "standard"))
      slab.system = raw.get("system", slab.system or "two_way")
      slab.reinforcement_data = raw.get("reinforcement_data", raw.get("reinforcementData"))
      slab.loads = raw.get("loads")
      slab.check_result = raw.get("check", raw.get("check_result"))
      slab.load_capacity = CalculationService.calculate_slab_load_capacity(slab.thickness, slab.area, slab.material)
      slab.floor_id = floor.id
      db.session.add(slab)
      seen_slabs.add(slab.client_id)

    for slab in list(floor.slabs):
      if slab.client_id not in seen_slabs:
        db.session.delete(slab)
    db.session.flush()
