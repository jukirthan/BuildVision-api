"""DTO helpers shared by the structure API.

The persistence layer uses SQLAlchemy's snake_case names while the planner
uses stable camelCase member DTOs. Keeping the conversion here prevents each
controller from inventing a slightly different mapping.
"""

import re


_SNAKE_PART = re.compile(r"_([a-zA-Z0-9])")


def snake_to_camel(value):
  if isinstance(value, list):
    return [snake_to_camel(item) for item in value]
  if isinstance(value, dict):
    return {snake_to_camel_key(key): snake_to_camel(item) for key, item in value.items()}
  return value


def camel_to_snake(value):
  if isinstance(value, list):
    return [camel_to_snake(item) for item in value]
  if isinstance(value, dict):
    return {camel_to_snake_key(key): camel_to_snake(item) for key, item in value.items()}
  return value


def snake_to_camel_key(key):
  return _SNAKE_PART.sub(lambda match: match.group(1).upper(), key)


def camel_to_snake_key(key):
  return re.sub(r"(?<!^)([A-Z])", r"_\1", key).lower()
