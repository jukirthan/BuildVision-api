from app.models.project import Project
from app.models.building import Building
from app.models.floor import Floor
from app.models.pillar import Pillar
from app.models.beam import Beam
from app.models.slab import Slab
from app.middleware import get_current_user
from app.services.building_service import BuildingService
from app.services.calculation_service import CalculationService
from app.utils import success_response, error_response


class DashboardController:
  @staticmethod
  def project_summary():
    current = get_current_user()
    if not current:
      return error_response("Unauthorized", 401)

    projects = Project.query.filter_by(user_id=current.id).all()
    summary = []
    for project in projects:
      buildings = Building.query.filter_by(project_id=project.id).all()
      floor_count = sum(
        Floor.query.filter_by(building_id=b.id).count() for b in buildings
      )
      summary.append({
        "project": project.to_dict(),
        "building_count": len(buildings),
        "floor_count": floor_count,
      })

    return success_response({
      "total_projects": len(projects),
      "projects": summary,
    })

  @staticmethod
  def building_statistics(building_id):
    current = get_current_user()
    building = Building.query.get(building_id)
    if not building:
      return error_response("Building not found", 404)

    project = Project.query.get(building.project_id)
    if project.user_id != current.id:
      return error_response("Forbidden", 403)

    stats = BuildingService.get_building_statistics(building_id)
    return success_response(stats)

  @staticmethod
  def material_information(floor_id):
    current = get_current_user()
    floor = Floor.query.get(floor_id)
    if not floor:
      return error_response("Floor not found", 404)

    building = Building.query.get(floor.building_id)
    project = Project.query.get(building.project_id)
    if project.user_id != current.id:
      return error_response("Forbidden", 403)

    materials = CalculationService.estimate_materials(floor_id)
    return success_response({
      "floor": floor.to_dict(),
      "materials": materials,
      "components": {
        "pillars": Pillar.query.filter_by(floor_id=floor_id).count(),
        "beams": Beam.query.filter_by(floor_id=floor_id).count(),
        "slabs": Slab.query.filter_by(floor_id=floor_id).count(),
      },
    })
