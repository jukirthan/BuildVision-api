import math
from app.extensions import db
from app.models.beam import Beam
from app.models.slab import Slab
from app.models.pillar import Pillar
from app.models.floor import Floor


class CalculationService:
  CONCRETE_DENSITY = 2400  # kg/m³
  STEEL_DENSITY = 7850  # kg/m³
  CONCRETE_COST_PER_M3 = 150.0
  STEEL_COST_PER_KG = 1.2

  @staticmethod
  def calculate_beam_length(start_x, start_y, end_x, end_y):
    return round(math.sqrt((end_x - start_x) ** 2 + (end_y - start_y) ** 2), 4)

  @staticmethod
  def calculate_beam_load_bearing(width, depth, length, material="concrete"):
    base = width * depth * length
    multiplier = 25.0 if material == "concrete" else 78.5
    return round(base * multiplier, 2)

  @staticmethod
  def calculate_slab_load_capacity(thickness, area, material="concrete"):
    volume = thickness * area
    multiplier = 25.0 if material == "concrete" else 78.5
    return round(volume * multiplier, 2)

  @staticmethod
  def calculate_pillar_load_capacity(width, depth, height, material="concrete"):
    volume = width * depth * height
    multiplier = 25.0 if material == "concrete" else 78.5
    return round(volume * multiplier * 10, 2)

  @staticmethod
  def recalculate_beams_for_floor(floor_id):
    beams = Beam.query.filter_by(floor_id=floor_id).all()
    for beam in beams:
      beam.length = CalculationService.calculate_beam_length(
        beam.start_x, beam.start_y, beam.end_x, beam.end_y
      )
      beam.load_bearing = CalculationService.calculate_beam_load_bearing(
        beam.width, beam.depth, beam.length, beam.material
      )
    return beams

  @staticmethod
  def recalculate_slabs_for_floor(floor_id):
    floor = Floor.query.get(floor_id)
    if not floor:
      return []
    slabs = Slab.query.filter_by(floor_id=floor_id).all()
    for slab in slabs:
      if not slab.area and floor.area:
        slab.area = floor.area
      slab.load_capacity = CalculationService.calculate_slab_load_capacity(
        slab.thickness, slab.area, slab.material
      )
    return slabs

  @staticmethod
  def recalculate_pillars_for_floor(floor_id):
    pillars = Pillar.query.filter_by(floor_id=floor_id).all()
    floor = Floor.query.get(floor_id)
    for pillar in pillars:
      if floor and not pillar.height:
        pillar.height = floor.height
      pillar.load_capacity = CalculationService.calculate_pillar_load_capacity(
        pillar.width, pillar.depth, pillar.height, pillar.material
      )
    return pillars

  @staticmethod
  def recalculate_floor_structure(floor_id):
    CalculationService.recalculate_pillars_for_floor(floor_id)
    CalculationService.recalculate_beams_for_floor(floor_id)
    CalculationService.recalculate_slabs_for_floor(floor_id)
    db.session.commit()

  @staticmethod
  def estimate_materials(floor_id):
    pillars = Pillar.query.filter_by(floor_id=floor_id).all()
    beams = Beam.query.filter_by(floor_id=floor_id).all()
    slabs = Slab.query.filter_by(floor_id=floor_id).all()

    concrete_volume = 0.0
    steel_weight = 0.0

    for pillar in pillars:
      concrete_volume += pillar.width * pillar.depth * pillar.height

    for beam in beams:
      concrete_volume += beam.width * beam.depth * beam.length
      steel_weight += beam.length * 0.5

    for slab in slabs:
      concrete_volume += slab.thickness * slab.area
      steel_weight += slab.area * 2.0

    return {
      "concrete_volume_m3": round(concrete_volume, 2),
      "steel_weight_kg": round(steel_weight, 2),
      "concrete_cost": round(concrete_volume * CalculationService.CONCRETE_COST_PER_M3, 2),
      "steel_cost": round(steel_weight * CalculationService.STEEL_COST_PER_KG, 2),
      "total_cost": round(
        concrete_volume * CalculationService.CONCRETE_COST_PER_M3
        + steel_weight * CalculationService.STEEL_COST_PER_KG,
        2,
      ),
      "pillar_count": len(pillars),
      "beam_count": len(beams),
      "slab_count": len(slabs),
    }

  @staticmethod
  def on_pillar_change(pillar):
    CalculationService.recalculate_floor_structure(pillar.floor_id)

  @staticmethod
  def on_beam_change(beam):
    beam.length = CalculationService.calculate_beam_length(
      beam.start_x, beam.start_y, beam.end_x, beam.end_y
    )
    beam.load_bearing = CalculationService.calculate_beam_load_bearing(
      beam.width, beam.depth, beam.length, beam.material
    )
    CalculationService.recalculate_slabs_for_floor(beam.floor_id)
    db.session.commit()

  @staticmethod
  def on_slab_change(slab):
    slab.load_capacity = CalculationService.calculate_slab_load_capacity(
      slab.thickness, slab.area, slab.material
    )
    db.session.commit()
