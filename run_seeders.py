from app import create_app
from app.extensions import db
from app.seeders import run_all_seeders

app = create_app()

with app.app_context():
  db.create_all()
  run_all_seeders()
