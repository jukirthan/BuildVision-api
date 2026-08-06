"""Pytest fixtures for BuildVision API tests (in-memory SQLite)."""

import pytest

from app import create_app
from app.extensions import db
from app.models.user import User


@pytest.fixture()
def app():
  application = create_app("testing")
  with application.app_context():
    db.create_all()
    yield application
    db.session.remove()
    db.drop_all()


@pytest.fixture()
def client(app):
  return app.test_client()


@pytest.fixture()
def admin_user(app):
  user = User(name="Admin", email="admin@test.com", role="admin")
  user.set_password("Admin123")
  db.session.add(user)
  db.session.commit()
  return user


@pytest.fixture()
def engineer_user(app):
  user = User(name="Engineer", email="eng@test.com", role="engineer")
  user.set_password("Engineer1")
  db.session.add(user)
  db.session.commit()
  return user


@pytest.fixture()
def viewer_user(app):
  user = User(name="Viewer", email="viewer@test.com", role="viewer")
  user.set_password("Viewer12")
  db.session.add(user)
  db.session.commit()
  return user


def auth_header(client, email, password):
  res = client.post(
    "/api/auth/login",
    json={"email": email, "password": password},
  )
  data = res.get_json()["data"]
  token = data.get("token") or data.get("access_token")
  return {"Authorization": f"Bearer {token}"}, data
