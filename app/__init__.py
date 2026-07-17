import logging
import os

from flask import Flask
from app.config import config_by_name
from app.extensions import db, migrate, jwt, cors

logger = logging.getLogger(__name__)


def initialize_database(app):
  with app.app_context():
    from app.models import user, project, building, floor, pillar, beam, slab  # noqa: F401
    try:
      db.create_all()
    except Exception as exc:
      # Do not crash the whole process on transient DB startup races.
      logger.exception("Database initialization failed: %s", exc)


def create_app(config_name=None):
  if config_name is None:
    config_name = os.getenv("FLASK_ENV", "production")

  app = Flask(__name__)
  app.config.from_object(config_by_name.get(config_name, config_by_name["production"]))

  db.init_app(app)
  migrate.init_app(app, db)
  jwt.init_app(app)
  cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

  from app.models import user, project, building, floor, pillar, beam, slab  # noqa: F401

  initialize_database(app)

  from app.routes.auth_routes import auth_bp
  from app.routes.user_routes import user_bp
  from app.routes.project_routes import project_bp
  from app.routes.building_routes import building_bp
  from app.routes.floor_routes import floor_bp
  from app.routes.pillar_routes import pillar_bp
  from app.routes.beam_routes import beam_bp
  from app.routes.slab_routes import slab_bp
  from app.routes.dashboard_routes import dashboard_bp

  app.register_blueprint(auth_bp, url_prefix="/api/auth")
  app.register_blueprint(user_bp, url_prefix="/api/users")
  app.register_blueprint(project_bp, url_prefix="/api/projects")
  app.register_blueprint(building_bp, url_prefix="/api/buildings")
  app.register_blueprint(floor_bp, url_prefix="/api/floors")
  app.register_blueprint(pillar_bp, url_prefix="/api/pillars")
  app.register_blueprint(beam_bp, url_prefix="/api/beams")
  app.register_blueprint(slab_bp, url_prefix="/api/slabs")
  app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")

  @app.route("/api/health")
  def health_check():
    return {"status": "ok", "service": "BuildVision 3D API"}, 200

  return app
