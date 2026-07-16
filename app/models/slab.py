from app.extensions import db
from app.utils import utc_now


class Slab(db.Model):
  __tablename__ = "slabs"

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100), nullable=False)
  thickness = db.Column(db.Float, default=0.15)
  area = db.Column(db.Float, default=0.0)
  material = db.Column(db.String(50), default="concrete")
  reinforcement = db.Column(db.String(100), default="standard")
  load_capacity = db.Column(db.Float, default=0.0)
  floor_id = db.Column(db.Integer, db.ForeignKey("floors.id"), nullable=False)
  created_at = db.Column(db.DateTime, default=utc_now)
  updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

  floor = db.relationship("Floor", back_populates="slabs")

  def to_dict(self):
    return {
      "id": self.id,
      "name": self.name,
      "thickness": self.thickness,
      "area": self.area,
      "material": self.material,
      "reinforcement": self.reinforcement,
      "load_capacity": self.load_capacity,
      "floor_id": self.floor_id,
      "created_at": self.created_at.isoformat() if self.created_at else None,
      "updated_at": self.updated_at.isoformat() if self.updated_at else None,
    }
