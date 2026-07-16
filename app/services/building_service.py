from app.extensions import db
from app.models.building import Building
from app.models.project import Project
from app.models.floor import Floor
from app.services.calculation_service import CalculationService


class BuildingService:
  @staticmethod
  def get_building_by_id(building_id):
    return Building.query.get(building_id)

  @staticmethod
  def get_buildings_by_project(project_id):
    return Building.query.filter_by(project_id=project_id).all()

  @staticmethod
  def create_building(data, project_id):
    project = Project.query.get(project_id)
    if not project:
      return None, "Project not found"

    building = Building(
      name=data["name"],
      building_type=data.get("building_type", "residential"),
      total_floors=data.get("total_floors", 1),
      width=data.get("width", 0.0),
      length=data.get("length", 0.0),
      height=data.get("height", 0.0),
      project_id=project_id,
    )
    db.session.add(building)
    db.session.commit()
    return building, None

  @staticmethod
  def update_building(building, data):
    for field in ["name", "building_type", "total_floors", "width", "length", "height"]:
      if field in data:
        setattr(building, field, data[field])
    db.session.commit()
    return building

  @staticmethod
  def delete_building(building):
    db.session.delete(building)
    db.session.commit()

  @staticmethod
  def get_building_statistics(building_id):
    building = Building.query.get(building_id)
    if not building:
      return None

    floors = Floor.query.filter_by(building_id=building_id).all()
    total_area = sum(f.area for f in floors)
    materials = {"concrete_volume_m3": 0, "steel_weight_kg": 0, "total_cost": 0}

    for floor in floors:
      floor_materials = CalculationService.estimate_materials(floor.id)
      materials["concrete_volume_m3"] += floor_materials["concrete_volume_m3"]
      materials["steel_weight_kg"] += floor_materials["steel_weight_kg"]
      materials["total_cost"] += floor_materials["total_cost"]

    return {
      "building": building.to_dict(),
      "floor_count": len(floors),
      "total_area": round(total_area, 2),
      "materials": {
        "concrete_volume_m3": round(materials["concrete_volume_m3"], 2),
        "steel_weight_kg": round(materials["steel_weight_kg"], 2),
        "total_cost": round(materials["total_cost"], 2),
      },
    }
