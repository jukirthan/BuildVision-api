from app.extensions import db
from app.utils import utc_now
from uuid import uuid4


class Beam(db.Model):
  __tablename__ = "beams"
  __table_args__ = (
    db.UniqueConstraint("floor_id", "client_id", name="uq_beam_floor_client"),
  )

  id = db.Column(db.Integer, primary_key=True)
  client_id = db.Column(db.String(36), nullable=False, default=lambda: str(uuid4()))
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
  start_pillar_id = db.Column(db.Integer, db.ForeignKey("pillars.id", ondelete="CASCADE"), nullable=True)
  end_pillar_id = db.Column(db.Integer, db.ForeignKey("pillars.id", ondelete="CASCADE"), nullable=True)
  concrete_grade = db.Column(db.String(20), default="M25")
  steel_grade = db.Column(db.String(20), default="Fe500")
  reinforcement = db.Column(db.JSON, nullable=True)
  support_condition = db.Column(db.String(30), default="continuous")
  loads = db.Column(db.JSON, nullable=True)
  check_result = db.Column(db.JSON, nullable=True)
  floor_id = db.Column(db.Integer, db.ForeignKey("floors.id"), nullable=False)
  created_at = db.Column(db.DateTime, default=utc_now)
  updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

  floor = db.relationship("Floor", back_populates="beams")

  def to_dict(self):
    return {
      "id": self.id,
      "client_id": self.client_id,
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
      "start_pillar_id": self.start_pillar_id,
      "end_pillar_id": self.end_pillar_id,
      "concrete_grade": self.concrete_grade,
      "steel_grade": self.steel_grade,
      "reinforcement": self.reinforcement,
      "support_condition": self.support_condition,
      "loads": self.loads,
      "check_result": self.check_result,
      "floor_id": self.floor_id,
      "created_at": self.created_at.isoformat() if self.created_at else None,
      "updated_at": self.updated_at.isoformat() if self.updated_at else None,
    }
