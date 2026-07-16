from app.extensions import db
from app.models.user import User
from app.models.project import Project
from app.models.building import Building
from app.models.floor import Floor
from app.models.pillar import Pillar
from app.models.beam import Beam
from app.models.slab import Slab
from app.services.calculation_service import CalculationService


def seed_admin_user():
  if User.query.filter_by(email="admin@buildvision.com").first():
    return User.query.filter_by(email="admin@buildvision.com").first()

  admin = User(
    name="Admin User",
    email="admin@buildvision.com",
    role="admin",
  )
  admin.set_password("admin123")
  db.session.add(admin)
  db.session.commit()
  return admin


def seed_sample_project(user):
  if Project.query.filter_by(name="Downtown Office Complex").first():
    return Project.query.filter_by(name="Downtown Office Complex").first()

  project = Project(
    name="Downtown Office Complex",
    description="A 5-story commercial office building with modern structural design",
    location="Colombo, Sri Lanka",
    status="in_progress",
    user_id=user.id,
  )
  db.session.add(project)
  db.session.commit()
  return project


def seed_sample_building(project):
  if Building.query.filter_by(name="Tower A").first():
    return Building.query.filter_by(name="Tower A").first()

  building = Building(
    name="Tower A",
    building_type="commercial",
    total_floors=3,
    width=30.0,
    length=20.0,
    height=12.0,
    project_id=project.id,
  )
  db.session.add(building)
  db.session.commit()
  return building


def seed_sample_floors(building):
  floors = []
  for i in range(1, 4):
    existing = Floor.query.filter_by(building_id=building.id, floor_number=i).first()
    if existing:
      floors.append(existing)
      continue
    floor = Floor(
      name=f"Floor {i}",
      floor_number=i,
      height=3.5,
      area=building.width * building.length,
      building_id=building.id,
    )
    db.session.add(floor)
    floors.append(floor)
  db.session.commit()
  return floors


def seed_sample_pillars(floor):
  positions = [(0, 0), (10, 0), (20, 0), (0, 15), (10, 15), (20, 15)]
  pillars = []
  for idx, (x, y) in enumerate(positions):
    name = f"P{floor.floor_number}-{idx + 1}"
    if Pillar.query.filter_by(name=name, floor_id=floor.id).first():
      continue
    pillar = Pillar(
      name=name,
      x_position=x,
      y_position=y,
      width=0.4,
      depth=0.4,
      height=floor.height,
      material="concrete",
      floor_id=floor.id,
    )
    pillar.load_capacity = CalculationService.calculate_pillar_load_capacity(
      pillar.width, pillar.depth, pillar.height, pillar.material
    )
    db.session.add(pillar)
    pillars.append(pillar)
  db.session.commit()
  return pillars


def seed_sample_beams(floor):
  beams_data = [
    {"name": f"B{floor.floor_number}-1", "start_x": 0, "start_y": 0, "end_x": 20, "end_y": 0},
    {"name": f"B{floor.floor_number}-2", "start_x": 0, "start_y": 15, "end_x": 20, "end_y": 15},
    {"name": f"B{floor.floor_number}-3", "start_x": 0, "start_y": 0, "end_x": 0, "end_y": 15},
  ]
  beams = []
  for data in beams_data:
    if Beam.query.filter_by(name=data["name"], floor_id=floor.id).first():
      continue
    beam = Beam(
      name=data["name"],
      start_x=data["start_x"],
      start_y=data["start_y"],
      end_x=data["end_x"],
      end_y=data["end_y"],
      width=0.3,
      depth=0.5,
      material="concrete",
      floor_id=floor.id,
    )
    beam.length = CalculationService.calculate_beam_length(
      beam.start_x, beam.start_y, beam.end_x, beam.end_y
    )
    beam.load_bearing = CalculationService.calculate_beam_load_bearing(
      beam.width, beam.depth, beam.length, beam.material
    )
    db.session.add(beam)
    beams.append(beam)
  db.session.commit()
  return beams


def seed_sample_slabs(floor):
  if Slab.query.filter_by(floor_id=floor.id).first():
    return []

  slab = Slab(
    name=f"Slab-F{floor.floor_number}",
    thickness=0.2,
    area=floor.area,
    material="concrete",
    reinforcement="standard",
    floor_id=floor.id,
  )
  slab.load_capacity = CalculationService.calculate_slab_load_capacity(
    slab.thickness, slab.area, slab.material
  )
  db.session.add(slab)
  db.session.commit()
  return [slab]


def run_all_seeders():
  print("Seeding admin user...")
  admin = seed_admin_user()
  print(f"  Admin user: {admin.email}")

  print("Seeding sample project...")
  project = seed_sample_project(admin)
  print(f"  Project: {project.name}")

  print("Seeding sample building...")
  building = seed_sample_building(project)
  print(f"  Building: {building.name}")

  print("Seeding floors...")
  floors = seed_sample_floors(building)
  print(f"  Floors: {len(floors)}")

  for floor in floors:
    print(f"  Seeding components for {floor.name}...")
    seed_sample_pillars(floor)
    seed_sample_beams(floor)
    seed_sample_slabs(floor)

  print("Seeding complete!")
