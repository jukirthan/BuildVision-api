from datetime import datetime, timezone


def success_response(data=None, message="Success", status_code=200):
  response = {"success": True, "message": message}
  if data is not None:
    response["data"] = data
  return response, status_code


def error_response(message="Error", status_code=400, errors=None):
  response = {"success": False, "message": message}
  if errors:
    response["errors"] = errors
  return response, status_code


def utc_now():
  return datetime.now(timezone.utc)


def validate_required_fields(data, required_fields):
  missing = [field for field in required_fields if not data.get(field)]
  if missing:
    return f"Missing required fields: {', '.join(missing)}"
  return None


def model_to_dict(obj, exclude=None):
  exclude = exclude or []
  result = {}
  for column in obj.__table__.columns:
    if column.name not in exclude:
      value = getattr(obj, column.name)
      if hasattr(value, "isoformat"):
        value = value.isoformat()
      result[column.name] = value
  return result
