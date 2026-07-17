import os
from datetime import timedelta
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()


def _build_database_uri():
  """Resolve DB URL for local MySQL and Railway MySQL plugin vars."""
  database_url = (
    os.getenv("DATABASE_URL")
    or os.getenv("MYSQL_URL")
    or os.getenv("MYSQL_PRIVATE_URL")
    or os.getenv("RAILWAY_DATABASE_URL")
  )

  if database_url:
    if database_url.startswith("mysql://"):
      database_url = database_url.replace("mysql://", "mysql+pymysql://", 1)
    elif database_url.startswith("mariadb://"):
      database_url = database_url.replace("mariadb://", "mysql+pymysql://", 1)
    return database_url

  db_host = os.getenv("MYSQLHOST") or os.getenv("DB_HOST", "localhost")
  db_port = os.getenv("MYSQLPORT") or os.getenv("DB_PORT", "3306")
  db_name = os.getenv("MYSQLDATABASE") or os.getenv("DB_NAME", "")
  db_user = os.getenv("MYSQLUSER") or os.getenv("DB_USER", "root")
  db_password = os.getenv("MYSQLPASSWORD") or os.getenv("DB_PASSWORD", "")

  user = quote_plus(db_user)
  password = quote_plus(db_password)
  return f"mysql+pymysql://{user}:{password}@{db_host}:{db_port}/{db_name}"


class Config:
  SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
  JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
  JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
  JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

  SQLALCHEMY_DATABASE_URI = _build_database_uri()
  SQLALCHEMY_TRACK_MODIFICATIONS = False
  SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_pre_ping": True,
    "pool_recycle": 280,
  }

  DEBUG = os.getenv("FLASK_ENV", "development") == "development"


class DevelopmentConfig(Config):
  DEBUG = True


class ProductionConfig(Config):
  DEBUG = False


config_by_name = {
  "development": DevelopmentConfig,
  "production": ProductionConfig,
}
