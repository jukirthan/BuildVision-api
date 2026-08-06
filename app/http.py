"""Register HTTP error handlers and security headers."""

from __future__ import annotations

from flask import Flask, jsonify, request

from app.errors import AppError
from app.utils import error_response


def register_error_handlers(app: Flask) -> None:
  @app.errorhandler(AppError)
  def handle_app_error(exc: AppError):
    body, status = error_response(exc.message, exc.status_code, errors=exc.errors)
    if isinstance(body, dict):
      body["code"] = getattr(exc, "code", "app_error")
    return body, status

  @app.errorhandler(404)
  def handle_404(_exc):
    return error_response("Not found", 404)

  @app.errorhandler(405)
  def handle_405(_exc):
    return error_response("Method not allowed", 405)

  @app.errorhandler(500)
  def handle_500(exc):
    app.logger.exception("Unhandled server error: %s", exc)
    return error_response("Internal server error", 500)


def register_security_headers(app: Flask) -> None:
  @app.after_request
  def set_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
      "Permissions-Policy", "camera=(self), microphone=(), geolocation=()"
    )
    # API responses — CSP is primarily for HTML; keep a tight default.
    if request.path.startswith("/api"):
      response.headers.setdefault(
        "Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'"
      )
    return response
