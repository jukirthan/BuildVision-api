from app.extensions import db
from app.utils import utc_now


class Beam(db.Model):
  __tablename__ = "beams"

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100), nullable=False)
  start_x = db.Column(db.Float, default=0.0)
  start_y = db.Column(db.Float, default=0.0)
  end_x = db.Column(db.Float, default=0.0)
  end_y = db.Column(db.Float, default=0.0)
  width = db.Column(db.Float, default=0.25)
  depth = db.Column(db.Float, default=0.4)
  length = db.Column(db.Float, default=0.0)
  material = db.Column(db.String(50), default="concrete")
  load_bearing = db.Column(db.Float, default=0.0)
  floor_id = db.Column(db.Integer, db.ForeignKey("floors.id"), nullable=False)
  created_at = db.Column(db.DateTime, default=utc_now)
  updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

  floor = db.relationship("Floor", back_populates="beams")

  def to_dict(self):
    return {
      "id": self.id,
      "name": self.name,
      "start_x": self.start_x,
      "start_y": self.start_y,
      "end_x": self.end_x,
      "end_y": self.end_y,
      "width": self.width,
      "depth": self.depth,
      "length": self.length,
      "material": self.material,
      "load_bearing": self.load_bearing,
      "floor_id": self.floor_id,
      "created_at": self.created_at.isoformat() if self.created_at else None,
      "updated_at": self.updated_at.isoformat() if self.updated_at else None,
    }
