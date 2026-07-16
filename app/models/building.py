from app.extensions import db
from app.utils import utc_now


class Building(db.Model):
  __tablename__ = "buildings"

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(200), nullable=False)
  building_type = db.Column(db.String(100), default="residential")
  total_floors = db.Column(db.Integer, default=1)
  width = db.Column(db.Float, default=0.0)
  length = db.Column(db.Float, default=0.0)
  height = db.Column(db.Float, default=0.0)
  project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
  created_at = db.Column(db.DateTime, default=utc_now)
  updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

  project = db.relationship("Project", back_populates="buildings")
  floors = db.relationship("Floor", back_populates="building", cascade="all, delete-orphan")

  def to_dict(self, include_floors=False):
    data = {
      "id": self.id,
      "name": self.name,
      "building_type": self.building_type,
      "total_floors": self.total_floors,
      "width": self.width,
      "length": self.length,
      "height": self.height,
      "project_id": self.project_id,
      "created_at": self.created_at.isoformat() if self.created_at else None,
      "updated_at": self.updated_at.isoformat() if self.updated_at else None,
    }
    if include_floors:
      data["floors"] = [f.to_dict() for f in self.floors]
    return data
