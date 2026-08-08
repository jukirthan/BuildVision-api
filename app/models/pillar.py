from app.extensions import db
from app.utils import utc_now
from uuid import uuid4


class Pillar(db.Model):
  __tablename__ = "pillars"
  __table_args__ = (
    db.UniqueConstraint("floor_id", "client_id", name="uq_pillar_floor_client"),
  )

  id = db.Column(db.Integer, primary_key=True)
  client_id = db.Column(db.String(36), nullable=False, default=lambda: str(uuid4()))
  name = db.Column(db.String(100), nullable=False)
  x_position = db.Column(db.Float, default=0.0)
  y_position = db.Column(db.Float, default=0.0)
  width = db.Column(db.Float, default=0.3)
  depth = db.Column(db.Float, default=0.3)
  height = db.Column(db.Float, default=3.0)
  material = db.Column(db.String(50), default="concrete")
  load_capacity = db.Column(db.Float, default=0.0)
  stack_id = db.Column(db.String(100), nullable=True, index=True)
  base_elevation = db.Column(db.Float, default=0.0, nullable=False)
  concrete_grade = db.Column(db.String(20), default="M25")
  steel_grade = db.Column(db.String(20), default="Fe500")
  clear_cover_mm = db.Column(db.Float, default=40.0)
  shape = db.Column(db.String(30), default="square")
  rotation_deg = db.Column(db.Float, default=0.0)
  reinforcement = db.Column(db.JSON, nullable=True)
  loads = db.Column(db.JSON, nullable=True)
  check_result = db.Column(db.JSON, nullable=True)
  floor_id = db.Column(db.Integer, db.ForeignKey("floors.id"), nullable=False)
  created_at = db.Column(db.DateTime, default=utc_now)
  updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

  floor = db.relationship("Floor", back_populates="pillars")

  def to_dict(self):
    return {
      "id": self.id,
      "client_id": self.client_id,
      "name": self.name,
      "x_position": self.x_position,
      "y_position": self.y_position,
      "width": self.width,
      "depth": self.depth,
      "height": self.height,
      "material": self.material,
      "load_capacity": self.load_capacity,
      "stack_id": self.stack_id,
      "base_elevation": self.base_elevation,
      "concrete_grade": self.concrete_grade,
      "steel_grade": self.steel_grade,
      "clear_cover_mm": self.clear_cover_mm,
      "shape": self.shape,
      "rotation_deg": self.rotation_deg,
      "reinforcement": self.reinforcement,
      "loads": self.loads,
      "check_result": self.check_result,
      "floor_id": self.floor_id,
      "created_at": self.created_at.isoformat() if self.created_at else None,
      "updated_at": self.updated_at.isoformat() if self.updated_at else None,
    }
