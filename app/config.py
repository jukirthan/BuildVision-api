import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
  SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
  JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
  JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
  JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

  DB_HOST = os.getenv("DB_HOST", "localhost")
  DB_PORT = os.getenv("DB_PORT", "3306")
  DB_NAME = os.getenv("DB_NAME", "")
  DB_USER = os.getenv("DB_USER", "root")
  DB_PASSWORD = os.getenv("DB_PASSWORD", "")

  SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or os.getenv("RAILWAY_DATABASE_URL")
  if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("mysql://"):
    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("mysql://", "mysql+pymysql://", 1)
  else:
    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI or (
      f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

  SQLALCHEMY_TRACK_MODIFICATIONS = False

  DEBUG = os.getenv("FLASK_ENV", "development") == "development"


class DevelopmentConfig(Config):
  DEBUG = True


class ProductionConfig(Config):
  DEBUG = False


config_by_name = {
  "development": DevelopmentConfig,
  "production": ProductionConfig,
}
