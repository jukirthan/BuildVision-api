"""Workspace-wide analytics for the administrator dashboard.

Remote MySQL (Railway proxy) costs ~400ms+ per round-trip, so this endpoint:
  1. Never loads full tables into Python
  2. Uses at most two SQL statements (aggregates + list rows)
  3. Caches the payload briefly so refresh / re-navigation feels instant
"""

import json
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from app.extensions import db
from app.utils import success_response

TREND_DAYS = 14
CACHE_TTL_SEC = 20

_cache = {"expires": 0.0, "payload": None}


def _as_utc(value):
  if value is None:
    return None
  if isinstance(value, str):
    try:
      value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
      return None
  if value.tzinfo is None:
    return value.replace(tzinfo=timezone.utc)
  return value


def _daily_series(rows, days=TREND_DAYS):
  """rows: iterable of (date_or_datetime, count)."""
  today = datetime.now(timezone.utc).date()
  buckets = {today - timedelta(days=i): 0 for i in range(days)}
  for day, count in rows:
    if day is None:
      continue
    if hasattr(day, "date"):
      day = day.date()
    elif isinstance(day, str):
      try:
        day = datetime.fromisoformat(day).date()
      except ValueError:
        continue
    if day in buckets:
      buckets[day] = int(count or 0)
  return [
    {"date": day.isoformat(), "count": buckets[day]}
    for day in sorted(buckets.keys())
  ]


def _invalidate_overview_cache():
  _cache["expires"] = 0.0
  _cache["payload"] = None


class AdminController:
  @staticmethod
  def overview():
    now = time.monotonic()
    if _cache["payload"] is not None and now < _cache["expires"]:
      return success_response(_cache["payload"])

    # ── Query 1: every aggregate the dashboard needs (one round-trip) ──
    agg = db.session.execute(
      text(
        """
        SELECT JSON_OBJECT(
          'users', (SELECT COUNT(*) FROM users),
          'projects', (SELECT COUNT(*) FROM projects),
          'buildings', (SELECT COUNT(*) FROM buildings),
          'floors', (SELECT COUNT(*) FROM floors),
          'pillars', (SELECT COUNT(*) FROM pillars),
          'beams', (SELECT COUNT(*) FROM beams),
          'slabs', (SELECT COUNT(*) FROM slabs),
          'active_creators', (SELECT COUNT(DISTINCT user_id) FROM projects),
          'new_7d', (
            SELECT COUNT(*) FROM users
            WHERE created_at >= (UTC_TIMESTAMP() - INTERVAL 7 DAY)
          ),
          'new_30d', (
            SELECT COUNT(*) FROM users
            WHERE created_at >= (UTC_TIMESTAMP() - INTERVAL 30 DAY)
          ),
          'projects_7d', (
            SELECT COUNT(*) FROM projects
            WHERE created_at >= (UTC_TIMESTAMP() - INTERVAL 7 DAY)
          ),
          'projects_30d', (
            SELECT COUNT(*) FROM projects
            WHERE created_at >= (UTC_TIMESTAMP() - INTERVAL 30 DAY)
          ),
          'by_role', (
            SELECT JSON_OBJECTAGG(COALESCE(role, 'engineer'), cnt)
            FROM (
              SELECT role, COUNT(*) AS cnt FROM users GROUP BY role
            ) role_counts
          ),
          'signups_by_day', (
            SELECT JSON_ARRAYAGG(JSON_OBJECT('date', d, 'count', c))
            FROM (
              SELECT DATE(created_at) AS d, COUNT(*) AS c
              FROM users
              WHERE created_at >= (UTC_TIMESTAMP() - INTERVAL :trend_days DAY)
              GROUP BY DATE(created_at)
            ) s
          ),
          'projects_by_day', (
            SELECT JSON_ARRAYAGG(JSON_OBJECT('date', d, 'count', c))
            FROM (
              SELECT DATE(created_at) AS d, COUNT(*) AS c
              FROM projects
              WHERE created_at >= (UTC_TIMESTAMP() - INTERVAL :trend_days DAY)
              GROUP BY DATE(created_at)
            ) p
          ),
          'recent_projects', (
            SELECT JSON_ARRAYAGG(JSON_OBJECT(
              'id', rp.id,
              'name', rp.name,
              'description', rp.description,
              'location', rp.location,
              'status', rp.status,
              'user_id', rp.user_id,
              'created_at', rp.created_at,
              'updated_at', rp.updated_at,
              'owner_name', rp.owner_name,
              'owner_email', rp.owner_email
            ))
            FROM (
              SELECT
                p.id, p.name, p.description, p.location, p.status, p.user_id,
                p.created_at, p.updated_at,
                u.name AS owner_name, u.email AS owner_email
              FROM projects p
              LEFT JOIN users u ON u.id = p.user_id
              ORDER BY p.created_at DESC, p.id DESC
              LIMIT 6
            ) rp
          )
        ) AS payload
        """
      ),
      {"trend_days": TREND_DAYS},
    ).scalar()

    if isinstance(agg, str):
      agg = json.loads(agg)
    agg = agg or {}

    by_role_raw = agg.get("by_role") or {}
    if isinstance(by_role_raw, str):
      by_role_raw = json.loads(by_role_raw)
    by_role = {
      str(k).lower(): int(v) for k, v in (by_role_raw or {}).items()
    }

    signup_raw = agg.get("signups_by_day") or []
    if isinstance(signup_raw, str):
      signup_raw = json.loads(signup_raw)
    project_day_raw = agg.get("projects_by_day") or []
    if isinstance(project_day_raw, str):
      project_day_raw = json.loads(project_day_raw)

    signups_by_day = _daily_series(
      [(row.get("date"), row.get("count")) for row in (signup_raw or [])]
    )
    projects_by_day = _daily_series(
      [(row.get("date"), row.get("count")) for row in (project_day_raw or [])]
    )

    # ── Query 2: list rows only (users + counts + recent projects) ────
    # LEFT OUTER JOIN so users with zero projects still appear.
    list_rows = db.session.execute(
      text(
        """
        SELECT
          u.id, u.name, u.email, u.role, u.created_at, u.updated_at,
          COALESCE(pc.project_count, 0) AS project_count,
          COALESCE(bc.building_count, 0) AS building_count
        FROM users u
        LEFT JOIN (
          SELECT user_id, COUNT(*) AS project_count
          FROM projects
          GROUP BY user_id
        ) pc ON pc.user_id = u.id
        LEFT JOIN (
          SELECT p.user_id, COUNT(b.id) AS building_count
          FROM projects p
          LEFT JOIN buildings b ON b.project_id = p.id
          GROUP BY p.user_id
        ) bc ON bc.user_id = u.id
        """
      )
    ).mappings().all()

    def user_payload(row):
      created = row["created_at"]
      updated = row["updated_at"]
      return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "role": row["role"],
        "created_at": created.isoformat() if created else None,
        "updated_at": updated.isoformat() if updated else None,
        "project_count": int(row["project_count"] or 0),
        "building_count": int(row["building_count"] or 0),
      }

    ranked = sorted(
      list_rows,
      key=lambda r: (
        int(r["project_count"] or 0),
        int(r["building_count"] or 0),
        r["id"],
      ),
      reverse=True,
    )[:5]

    recent_users = sorted(
      list_rows,
      key=lambda r: (
        _as_utc(r["created_at"]) or datetime.min.replace(tzinfo=timezone.utc),
        r["id"],
      ),
      reverse=True,
    )[:5]

    recent_project_raw = agg.get("recent_projects") or []
    if isinstance(recent_project_raw, str):
      recent_project_raw = json.loads(recent_project_raw)

    def _iso(value):
      if value is None:
        return None
      if hasattr(value, "isoformat"):
        return value.isoformat()
      return str(value)

    recent_projects = [
      {
        "id": r.get("id"),
        "name": r.get("name"),
        "description": r.get("description"),
        "location": r.get("location"),
        "status": r.get("status"),
        "user_id": r.get("user_id"),
        "created_at": _iso(r.get("created_at")),
        "updated_at": _iso(r.get("updated_at")),
        "owner_name": r.get("owner_name"),
        "owner_email": r.get("owner_email"),
      }
      for r in (recent_project_raw or [])
    ]

    total_users = int(agg.get("users") or 0)
    total_projects = int(agg.get("projects") or 0)
    total_buildings = int(agg.get("buildings") or 0)

    payload = {
      "users": {
        "total": total_users,
        "by_role": by_role,
        "new_7d": int(agg.get("new_7d") or 0),
        "new_30d": int(agg.get("new_30d") or 0),
        "active_creators": int(agg.get("active_creators") or 0),
      },
      "content": {
        "projects": total_projects,
        "buildings": total_buildings,
        "floors": int(agg.get("floors") or 0),
        "pillars": int(agg.get("pillars") or 0),
        "beams": int(agg.get("beams") or 0),
        "slabs": int(agg.get("slabs") or 0),
      },
      "averages": {
        "projects_per_user": (
          round(total_projects / total_users, 2) if total_users else 0
        ),
        "buildings_per_project": (
          round(total_buildings / total_projects, 2) if total_projects else 0
        ),
      },
      "activity": {
        "projects_7d": int(agg.get("projects_7d") or 0),
        "projects_30d": int(agg.get("projects_30d") or 0),
        "signups_by_day": signups_by_day,
        "projects_by_day": projects_by_day,
      },
      "top_users": [user_payload(r) for r in ranked],
      "recent_users": [user_payload(r) for r in recent_users],
      "recent_projects": recent_projects,
    }

    _cache["payload"] = payload
    _cache["expires"] = time.monotonic() + CACHE_TTL_SEC
    return success_response(payload)
