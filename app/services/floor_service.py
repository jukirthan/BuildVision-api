from app.extensions import db
from app.models.floor import Floor
from app.models.building import Building
from app.services.calculation_service import CalculationService


class FloorService:
  @staticmethod
  def get_floor_by_id(floor_id):
    return Floor.query.get(floor_id)

  @staticmethod
  def get_floors_by_building(building_id):
    return Floor.query.filter_by(building_id=building_id).order_by(Floor.floor_number).all()

  @staticmethod
  def create_floor(data, building_id):
    building = Building.query.get(building_id)
    if not building:
      return None, "Building not found"

    floor = Floor(
      name=data["name"],
      floor_number=data["floor_number"],
      height=data.get("height", 3.0),
      area=data.get("area", building.width * building.length if building.width and building.length else 0.0),
      building_id=building_id,
    )
    db.session.add(floor)
    db.session.commit()
    return floor, None

  @staticmethod
  def update_floor(floor, data):
    for field in ["name", "floor_number", "height", "area"]:
      if field in data:
        setattr(floor, field, data[field])
    db.session.commit()
    CalculationService.recalculate_floor_structure(floor.id)
    return floor

  @staticmethod
  def delete_floor(floor):
    db.session.delete(floor)
    db.session.commit()

  @staticmethod
  def get_floor_with_components(floor_id):
    floor = Floor.query.get(floor_id)
    if not floor:
      return None
    return floor.to_dict(include_components=True)
