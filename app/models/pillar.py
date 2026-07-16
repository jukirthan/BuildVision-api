from app.extensions import db
from app.utils import utc_now


class Pillar(db.Model):
  __tablename__ = "pillars"

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100), nullable=False)
  x_position = db.Column(db.Float, default=0.0)
  y_position = db.Column(db.Float, default=0.0)
  width = db.Column(db.Float, default=0.3)
  depth = db.Column(db.Float, default=0.3)
  height = db.Column(db.Float, default=3.0)
  material = db.Column(db.String(50), default="concrete")
  load_capacity = db.Column(db.Float, default=0.0)
  floor_id = db.Column(db.Integer, db.ForeignKey("floors.id"), nullable=False)
  created_at = db.Column(db.DateTime, default=utc_now)
  updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

  floor = db.relationship("Floor", back_populates="pillars")

  def to_dict(self):
    return {
      "id": self.id,
      "name": self.name,
      "x_position": self.x_position,
      "y_position": self.y_position,
      "width": self.width,
      "depth": self.depth,
      "height": self.height,
      "material": self.material,
      "load_capacity": self.load_capacity,
      "floor_id": self.floor_id,
      "created_at": self.created_at.isoformat() if self.created_at else None,
      "updated_at": self.updated_at.isoformat() if self.updated_at else None,
    }
