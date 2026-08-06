"""Application-level errors and HTTP mappings."""

from __future__ import annotations


class AppError(Exception):
  """Base API error with an HTTP status and optional field errors."""

  status_code = 400
  code = "app_error"

  def __init__(self, message: str = "Request failed", *, errors=None):
    super().__init__(message)
    self.message = message
    self.errors = errors


class UnauthorizedError(AppError):
  status_code = 401
  code = "unauthorized"

  def __init__(self, message: str = "Unauthorized"):
    super().__init__(message)


class ForbiddenError(AppError):
  status_code = 403
  code = "forbidden"

  def __init__(self, message: str = "Forbidden"):
    super().__init__(message)


class NotFoundError(AppError):
  status_code = 404
  code = "not_found"

  def __init__(self, message: str = "Not found"):
    super().__init__(message)


class ValidationError(AppError):
  status_code = 422
  code = "validation_error"

  def __init__(self, message: str = "Validation failed", *, errors=None):
    super().__init__(message, errors=errors)


class ConflictError(AppError):
  status_code = 409
  code = "conflict"

  def __init__(self, message: str = "Conflict"):
    super().__init__(message)
