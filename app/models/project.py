from app.extensions import db
from app.utils import utc_now


class Project(db.Model):
  __tablename__ = "projects"

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(200), nullable=False)
  description = db.Column(db.Text)
  location = db.Column(db.String(200))
  status = db.Column(db.String(50), default="planning")
  user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
  created_at = db.Column(db.DateTime, default=utc_now)
  updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

  owner = db.relationship("User", back_populates="projects")
  buildings = db.relationship("Building", back_populates="project", cascade="all, delete-orphan")

  def to_dict(self, include_buildings=False):
    data = {
      "id": self.id,
      "name": self.name,
      "description": self.description,
      "location": self.location,
      "status": self.status,
      "user_id": self.user_id,
      "created_at": self.created_at.isoformat() if self.created_at else None,
      "updated_at": self.updated_at.isoformat() if self.updated_at else None,
    }
    if include_buildings:
      data["buildings"] = [b.to_dict() for b in self.buildings]
    return data
