import logging
import os
import tempfile
import threading
import time

from flask import Flask
from app.config import config_by_name
from app.extensions import db, migrate, jwt, cors
from app.http import register_error_handlers, register_security_headers

logger = logging.getLogger(__name__)

# Guards against multiple concurrent requests within the same worker process
# triggering database initialization at the same time.
_init_lock = threading.Lock()

# Cross-process file lock so that, when running under gunicorn with multiple
# worker processes, only one worker performs the (blocking) DDL work while
# the others wait/skip once it has completed.
_DB_INIT_LOCK_PATH = os.path.join(tempfile.gettempdir(), "buildvision_db_init.lock")

_MAX_RETRIES = 3
_RETRY_DELAY_SECONDS = 1


def _run_database_ddl(app):
  with app.app_context():
    from app.models import user, project, building, floor, pillar, beam, slab  # noqa: F401
    db.create_all()


def initialize_database(app):
  """Initialize the database schema, guarded by an in-process lock and a
  cross-process file lock, with retries for transient failures.

  This is intentionally NOT called during create_app(): it performs
  blocking I/O (DDL) and running it synchronously during app creation
  delays gunicorn startup and can cause worker boot log ordering issues.
  Instead, it is invoked lazily on the first incoming request.
  """
  with _init_lock:
    if app.config.get("_DB_INITIALIZED"):
      return

    lock_file = None
    try:
      try:
        import fcntl

        lock_file = open(_DB_INIT_LOCK_PATH, "w")
        fcntl.flock(lock_file, fcntl.LOCK_EX)
      except (ImportError, OSError):
        # fcntl is unavailable (e.g. non-POSIX platforms) — fall back to
        # relying solely on the in-process lock.
        lock_file = None

      last_exc = None
      for attempt in range(1, _MAX_RETRIES + 1):
        try:
          _run_database_ddl(app)
          last_exc = None
          break
        except Exception as exc:  # noqa: BLE001
          last_exc = exc
          logger.warning(
            "Database initialization attempt %s/%s failed: %s",
            attempt,
            _MAX_RETRIES,
            exc,
          )
          if attempt < _MAX_RETRIES:
            time.sleep(_RETRY_DELAY_SECONDS * attempt)

      if last_exc is not None:
        # Do not crash the whole process on transient DB startup races.
        logger.exception("Database initialization failed after %s attempts: %s", _MAX_RETRIES, last_exc)
      else:
        app.config["_DB_INITIALIZED"] = True
    finally:
      if lock_file is not None:
        try:
          import fcntl

          fcntl.flock(lock_file, fcntl.LOCK_UN)
        except (ImportError, OSError):
          pass
        lock_file.close()


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

  # Database initialization performs blocking DDL work. Running it here,
  # synchronously during create_app(), delays gunicorn startup and causes
  # worker boot log ordering issues (workers appear to finish booting
  # before gunicorn even prints its "Starting gunicorn" banner). Instead,
  # defer it to the first incoming request via a before_request hook so the
  # app object is ready — and gunicorn can start serving — immediately.
  if not app.config.get("TESTING"):
    app.config["_DB_INITIALIZED"] = False

    @app.before_request
    def _lazy_initialize_database():
      if not app.config.get("_DB_INITIALIZED"):
        initialize_database(app)

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
