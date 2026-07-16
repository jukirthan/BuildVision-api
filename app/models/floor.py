from app.extensions import db
from app.utils import utc_now


class Floor(db.Model):
  __tablename__ = "floors"

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100), nullable=False)
  floor_number = db.Column(db.Integer, nullable=False)
  height = db.Column(db.Float, default=3.0)
  area = db.Column(db.Float, default=0.0)
  building_id = db.Column(db.Integer, db.ForeignKey("buildings.id"), nullable=False)
  created_at = db.Column(db.DateTime, default=utc_now)
  updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

  building = db.relationship("Building", back_populates="floors")
  pillars = db.relationship("Pillar", back_populates="floor", cascade="all, delete-orphan")
  beams = db.relationship("Beam", back_populates="floor", cascade="all, delete-orphan")
  slabs = db.relationship("Slab", back_populates="floor", cascade="all, delete-orphan")

  def to_dict(self, include_components=False):
    data = {
      "id": self.id,
      "name": self.name,
      "floor_number": self.floor_number,
      "height": self.height,
      "area": self.area,
      "building_id": self.building_id,
      "created_at": self.created_at.isoformat() if self.created_at else None,
      "updated_at": self.updated_at.isoformat() if self.updated_at else None,
    }
    if include_components:
      data["pillars"] = [p.to_dict() for p in self.pillars]
      data["beams"] = [b.to_dict() for b in self.beams]
      data["slabs"] = [s.to_dict() for s in self.slabs]
    return data
