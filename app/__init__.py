import logging
import os
import threading

from flask import Flask
from app.config import config_by_name
from app.extensions import db, migrate, jwt, cors
from app.http import register_error_handlers, register_security_headers

logger = logging.getLogger(__name__)

_db_init_lock = threading.Lock()


def initialize_database(app):
  with app.app_context():
    from app.models import user, project, building, floor, pillar, beam, slab  # noqa: F401
    try:
      db.create_all()
    except Exception as exc:
      # Do not crash the whole process on transient DB startup races.
      logger.exception("Database initialization failed: %s", exc)


def _register_api_blueprints(app, prefix: str, name_suffix: str = ""):
  """Mount the same resource blueprints under /api and /api/v1."""
  from app.routes.auth_routes import auth_bp
  from app.routes.user_routes import user_bp
  from app.routes.project_routes import project_bp
  from app.routes.building_routes import building_bp
  from app.routes.floor_routes import floor_bp
  from app.routes.pillar_routes import pillar_bp
  from app.routes.beam_routes import beam_bp
  from app.routes.slab_routes import slab_bp
  from app.routes.dashboard_routes import dashboard_bp
  from app.routes.ai_routes import ai_bp
  from app.routes.recommendation_routes import recommendation_bp
  from app.routes.admin_routes import admin_bp

  pairs = [
    (auth_bp, "auth"),
    (user_bp, "users"),
    (project_bp, "projects"),
    (building_bp, "buildings"),
    (floor_bp, "floors"),
    (pillar_bp, "pillars"),
    (beam_bp, "beams"),
    (slab_bp, "slabs"),
    (dashboard_bp, "dashboard"),
    (ai_bp, "ai"),
    (recommendation_bp, "recommendations"),
    (admin_bp, "admin"),
  ]

  for bp, name in pairs:
    kwargs = {"url_prefix": f"{prefix}/{name}"}
    if name_suffix:
      kwargs["name"] = f"{bp.name}{name_suffix}"
    app.register_blueprint(bp, **kwargs)


def create_app(config_name=None):
  if config_name is None:
    config_name = os.getenv("FLASK_ENV", "production")

  app = Flask(__name__)
  app.config.from_object(config_by_name.get(config_name, config_by_name["production"]))

  # Accept both "/api/projects" and "/api/projects/" without redirecting.
  # A 3xx redirect here can cross origins (e.g. when proxied through the
  # Next.js dev server) and strip the Authorization header on the hop,
  # breaking authenticated POST/PUT requests such as "create project".
  app.url_map.strict_slashes = False

  db.init_app(app)
  migrate.init_app(app, db)
  jwt.init_app(app)
  cors.init_app(
    app,
    resources={
      r"/api/*": {
        "origins": app.config.get("CORS_ORIGINS", ["http://localhost:3000"]),
        "supports_credentials": True,
      }
    },
  )

  from app.models import user, project, building, floor, pillar, beam, slab  # noqa: F401

  if not app.config.get("TESTING"):
    @app.before_request
    def _lazy_db_init():
      if not app.config.get("_DB_INITIALIZED"):
        with _db_init_lock:
          if not app.config.get("_DB_INITIALIZED"):
            initialize_database(app)
            app.config["_DB_INITIALIZED"] = True

  _register_api_blueprints(app, "/api")
  _register_api_blueprints(app, "/api/v1", name_suffix="_v1")

  def health_payload():
    from app.utils import success_response

    return success_response(
      {
        "status": "ok",
        "service": "BuildVision 3D API",
        "api_versions": ["v1"],
      },
      "API healthy",
    )

  app.add_url_rule("/api/health", endpoint="health", view_func=health_payload)
  app.add_url_rule("/api/v1/health", endpoint="health_v1", view_func=health_payload)

  register_error_handlers(app)
  register_security_headers(app)

  return app
