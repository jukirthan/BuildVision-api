"""Workspace-wide analytics for the administrator dashboard.

An admin does not design buildings — they oversee accounts and adoption.
Everything here is aggregate: who is on the platform, what they have
created, and how that is trending.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func

from app.extensions import db
from app.models.user import User
from app.models.project import Project
from app.models.building import Building
from app.models.floor import Floor
from app.models.pillar import Pillar
from app.models.beam import Beam
from app.models.slab import Slab
from app.utils import success_response

TREND_DAYS = 14


def _as_utc(value):
  """SQLite hands back naive datetimes; normalise before comparing."""
  if value is None:
    return None
  if value.tzinfo is None:
    return value.replace(tzinfo=timezone.utc)
  return value


def _count_since(values, days):
  cutoff = datetime.now(timezone.utc) - timedelta(days=days)
  return sum(1 for v in values if v and v >= cutoff)


def _daily_series(values, days=TREND_DAYS):
  """Bucket timestamps into one count per day, oldest first.

  Done in Python rather than SQL so the same code works on SQLite in dev
  and Postgres in production without dialect-specific date functions.
  """
  today = datetime.now(timezone.utc).date()
  buckets = {today - timedelta(days=i): 0 for i in range(days)}
  for v in values:
    if not v:
      continue
    day = v.date()
    if day in buckets:
      buckets[day] += 1
  return [
    {"date": day.isoformat(), "count": buckets[day]}
    for day in sorted(buckets.keys())
  ]


class AdminController:
  @staticmethod
  def overview():
    users = User.query.all()
    user_dates = [_as_utc(u.created_at) for u in users]

    projects = Project.query.all()
    project_dates = [_as_utc(p.created_at) for p in projects]

    by_role = {}
    for u in users:
      key = (u.role or "engineer").lower()
      by_role[key] = by_role.get(key, 0) + 1

    # Per-user activity, aggregated in single grouped queries.
    project_counts = dict(
      db.session.query(Project.user_id, func.count(Project.id))
      .group_by(Project.user_id)
      .all()
    )
    building_counts = dict(
      db.session.query(Project.user_id, func.count(Building.id))
      .join(Building, Building.project_id == Project.id)
      .group_by(Project.user_id)
      .all()
    )

    ranked = sorted(
      users,
      key=lambda u: (project_counts.get(u.id, 0), building_counts.get(u.id, 0)),
      reverse=True,
    )

    def user_row(u):
      row = u.to_dict()
      row["project_count"] = int(project_counts.get(u.id, 0))
      row["building_count"] = int(building_counts.get(u.id, 0))
      return row

    total_projects = len(projects)
    total_buildings = Building.query.count()

    owners = {u.id: u for u in users}
    recent_projects = sorted(
      projects, key=lambda p: _as_utc(p.created_at) or datetime.min.replace(tzinfo=timezone.utc), reverse=True
    )[:6]

    return success_response({
      "users": {
        "total": len(users),
        "by_role": by_role,
        "new_7d": _count_since(user_dates, 7),
        "new_30d": _count_since(user_dates, 30),
        "active_creators": sum(1 for u in users if project_counts.get(u.id, 0) > 0),
      },
      "content": {
        "projects": total_projects,
        "buildings": total_buildings,
        "floors": Floor.query.count(),
        "pillars": Pillar.query.count(),
        "beams": Beam.query.count(),
        "slabs": Slab.query.count(),
      },
      "averages": {
        "projects_per_user": round(total_projects / len(users), 2) if users else 0,
        "buildings_per_project": (
          round(total_buildings / total_projects, 2) if total_projects else 0
        ),
      },
      "activity": {
        "projects_7d": _count_since(project_dates, 7),
        "projects_30d": _count_since(project_dates, 30),
        "signups_by_day": _daily_series(user_dates),
        "projects_by_day": _daily_series(project_dates),
      },
      "top_users": [user_row(u) for u in ranked[:5]],
      "recent_users": [
        user_row(u)
        for u in sorted(
          users,
          key=lambda u: _as_utc(u.created_at) or datetime.min.replace(tzinfo=timezone.utc),
          reverse=True,
        )[:5]
      ],
      "recent_projects": [
        {
          **p.to_dict(),
          "owner_name": getattr(owners.get(p.user_id), "name", None),
          "owner_email": getattr(owners.get(p.user_id), "email", None),
        }
        for p in recent_projects
      ],
    })
