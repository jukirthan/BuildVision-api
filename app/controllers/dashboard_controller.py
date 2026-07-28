from app.models.project import Project
from app.models.building import Building
from app.models.floor import Floor
from app.models.pillar import Pillar
from app.models.beam import Beam
from app.models.slab import Slab
from app.access import get_building_for_user, get_floor_for_user, current_user_or_401
from app.services.building_service import BuildingService
from app.services.calculation_service import CalculationService
from app.utils import success_response


class DashboardController:
  @staticmethod
  def project_summary():
    current, err = current_user_or_401()
    if err:
      return err

    if getattr(current, "role", None) == "admin":
      projects = Project.query.all()
    else:
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
    _, _, err = get_building_for_user(building_id)
    if err:
      return err
    stats = BuildingService.get_building_statistics(building_id)
    return success_response(stats)

  @staticmethod
  def material_information(floor_id):
    _, floor, err = get_floor_for_user(floor_id)
    if err:
      return err

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
