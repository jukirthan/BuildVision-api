"""Password policy helpers."""

from __future__ import annotations

import re


MIN_PASSWORD_LENGTH = 8


def validate_password_strength(password: str) -> str | None:
  """Return an error message if the password is too weak, else None."""
  if not password or len(password) < MIN_PASSWORD_LENGTH:
    return f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
  if not re.search(r"[A-Za-z]", password):
    return "Password must include at least one letter"
  if not re.search(r"\d", password):
    return "Password must include at least one number"
  return None
