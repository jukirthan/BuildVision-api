from app.extensions import db
from app.utils import utc_now
from uuid import uuid4


class Slab(db.Model):
  __tablename__ = "slabs"
  __table_args__ = (
    db.UniqueConstraint("floor_id", "client_id", name="uq_slab_floor_client"),
  )

  id = db.Column(db.Integer, primary_key=True)
  client_id = db.Column(db.String(36), nullable=False, default=lambda: str(uuid4()))
  name = db.Column(db.String(100), nullable=False)
  thickness = db.Column(db.Float, default=0.15)
  area = db.Column(db.Float, default=0.0)
  material = db.Column(db.String(50), default="concrete")
  reinforcement = db.Column(db.String(100), default="standard")
  system = db.Column(db.String(30), default="two_way")
  reinforcement_data = db.Column(db.JSON, nullable=True)
  loads = db.Column(db.JSON, nullable=True)
  check_result = db.Column(db.JSON, nullable=True)
  load_capacity = db.Column(db.Float, default=0.0)
  floor_id = db.Column(db.Integer, db.ForeignKey("floors.id"), nullable=False)
  created_at = db.Column(db.DateTime, default=utc_now)
  updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

  floor = db.relationship("Floor", back_populates="slabs")

  def to_dict(self):
    return {
      "id": self.id,
      "client_id": self.client_id,
      "name": self.name,
      "thickness": self.thickness,
      "area": self.area,
      "material": self.material,
      "reinforcement": self.reinforcement,
      "system": self.system,
      "reinforcement_data": self.reinforcement_data,
      "loads": self.loads,
      "check_result": self.check_result,
      "load_capacity": self.load_capacity,
      "floor_id": self.floor_id,
      "created_at": self.created_at.isoformat() if self.created_at else None,
      "updated_at": self.updated_at.isoformat() if self.updated_at else None,
    }
