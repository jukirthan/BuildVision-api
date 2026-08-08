import errno
import logging
import os
import time

from flask import Flask
from sqlalchemy.exc import OperationalError
from app.config import config_by_name
from app.extensions import db, migrate, jwt, cors
from app.http import register_error_handlers, register_security_headers

logger = logging.getLogger(__name__)

# Path to a file-based lock used to serialize schema creation across
# concurrently starting instances/replicas on the same host/container.
_DB_INIT_LOCK_PATH = os.getenv("DB_INIT_LOCK_PATH", "/tmp/buildvision_db_init.lock")
_DB_INIT_MAX_RETRIES = 3
_DB_INIT_INITIAL_BACKOFF_SECONDS = 1


class _FileLock:
  """A tiny best-effort, cross-platform-ish file lock.

  Uses O_CREAT|O_EXCL to atomically create a lock file. This is not a
  perfect distributed lock (it only helps within a single filesystem,
  e.g. a single replica/container), but it is enough to stop multiple
  processes/threads on the same instance from racing to run DDL, and it
  degrades gracefully (falls through) if it can't acquire the lock.
  """

  def __init__(self, path, timeout=10, poll_interval=0.2):
    self.path = path
    self.timeout = timeout
    self.poll_interval = poll_interval
    self._fd = None

  def acquire(self):
    deadline = time.monotonic() + self.timeout
    while True:
      try:
        self._fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
        return True
      except FileExistsError:
        if time.monotonic() >= deadline:
          return False
        time.sleep(self.poll_interval)
      except OSError as exc:
        if exc.errno != errno.EEXIST:
          # Filesystem doesn't support the lock (e.g. read-only /tmp).
          # Fall back to running without a lock rather than failing startup.
          logger.warning("Unable to use DB init file lock at %s: %s", self.path, exc)
          return False
        if time.monotonic() >= deadline:
          return False
        time.sleep(self.poll_interval)

  def release(self):
    if self._fd is not None:
      try:
        os.close(self._fd)
      except OSError:
        pass
      self._fd = None
    try:
      os.remove(self.path)
    except OSError:
      pass

  def __enter__(self):
    self.acquire()
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    self.release()


def _create_all_with_retry():
  """Run db.create_all() with exponential backoff on concurrent DDL errors.

  MySQL raises OperationalError (1684) when another connection is
  concurrently altering the same table's schema. Retrying with backoff
  gives the other instance time to finish its DDL before we try again.
  """
  backoff = _DB_INIT_INITIAL_BACKOFF_SECONDS
  last_exc = None
  for attempt in range(1, _DB_INIT_MAX_RETRIES + 1):
    try:
      db.create_all()
      return True
    except OperationalError as exc:
      last_exc = exc
      logger.warning(
        "Database schema creation attempt %s/%s failed with a (likely "
        "concurrent DDL) OperationalError: %s",
        attempt,
        _DB_INIT_MAX_RETRIES,
        exc,
      )
      if attempt < _DB_INIT_MAX_RETRIES:
        time.sleep(backoff)
        backoff *= 2
      db.session.rollback()

  logger.error(
    "Database schema creation failed after %s attempts: %s",
    _DB_INIT_MAX_RETRIES,
    last_exc,
  )
  return False


def initialize_database(app):
  """Initialize the database schema.

  This is deliberately defensive: if the DDL fails after retries (e.g.
  another replica is doing the same work at the same time), we log and
  return rather than raising, so the app still starts and can serve
  requests. Callers can add their own lazy retry-on-first-request logic
  if strict "schema must exist" guarantees are required.
  """
  with app.app_context():
    from app.models import user, project, building, floor, pillar, beam, slab  # noqa: F401

    lock = _FileLock(_DB_INIT_LOCK_PATH)
    acquired = lock.acquire()
    if not acquired:
      logger.info(
        "Could not acquire DB init lock at %s within timeout; proceeding "
        "without it (schema creation is retried on OperationalError).",
        _DB_INIT_LOCK_PATH,
      )
    try:
      _create_all_with_retry()
    except Exception as exc:
      # Do not crash the whole process on transient DB startup races.
      logger.exception("Database initialization failed: %s", exc)
    finally:
      if acquired:
        lock.release()


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
