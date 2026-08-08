"""Small server-side OpenAI Responses API adapter.

The API key never crosses into the browser. Keeping this adapter isolated also
means the Flask route can return safe, user-facing errors without exposing
provider response bodies or credentials.
"""

import json
import logging
import os
import urllib.error
import urllib.request


logger = logging.getLogger(__name__)


class OpenAIServiceError(Exception):
  """An expected provider/configuration failure safe to show to the client."""


SYSTEM_PROMPT = """You are BuildVision's structural design assistant.
Give practical, concise guidance about architectural planning, reinforced
concrete concepts, quantities, floor layouts, and the BuildVision planner.
Use SI units when dimensions are discussed. State assumptions and important
uncertainties. Do not present concept advice as stamped engineering documents,
code compliance, or construction approval; recommend review by a licensed
architect or engineer when a decision affects safety or construction.
"""


def _extract_text(body):
  direct = body.get("output_text")
  if isinstance(direct, str) and direct.strip():
    return direct.strip()

  chunks = []
  for item in body.get("output", []) or []:
    for content in item.get("content", []) or []:
      if content.get("type") == "output_text" and isinstance(content.get("text"), str):
        chunks.append(content["text"])
  return "\n".join(chunks).strip()


def _provider_error(status):
  if status in (401, 403):
    return "OpenAI authentication failed. Set a valid OPENAI_API_KEY on the Flask backend."
  if status == 429:
    return "OpenAI rate limit reached. Please wait a moment and try again."
  if status >= 500:
    return "OpenAI is temporarily unavailable. Please try again shortly."
  return "OpenAI rejected the chat request. Check the backend model configuration."


def generate_chat_reply(messages):
  api_key = os.getenv("OPENAI_API_KEY", "").strip()
  if not api_key:
    raise OpenAIServiceError(
      "AI assistant is not configured. Add OPENAI_API_KEY to the Flask backend environment."
    )

  model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
  input_items = [
    {"role": "developer", "content": [{"type": "input_text", "text": SYSTEM_PROMPT}]},
  ]
  input_items.extend(
    {
      "role": message["role"],
      "content": [{"type": "input_text", "text": message["content"]}],
    }
    for message in messages
  )

  request_body = json.dumps(
    {
      "model": model,
      "input": input_items,
      "store": False,
      "max_output_tokens": 800,
    }
  ).encode("utf-8")
  request = urllib.request.Request(
    "https://api.openai.com/v1/responses",
    data=request_body,
    headers={
      "Authorization": f"Bearer {api_key}",
      "Content-Type": "application/json",
    },
    method="POST",
  )

  try:
    with urllib.request.urlopen(request, timeout=35) as response:
      body = json.loads(response.read().decode("utf-8"))
  except urllib.error.HTTPError as exc:
    logger.warning("OpenAI Responses API returned HTTP %s", exc.code)
    raise OpenAIServiceError(_provider_error(exc.code)) from exc
  except (urllib.error.URLError, TimeoutError) as exc:
    logger.warning("OpenAI Responses API connection failed: %s", exc.reason if hasattr(exc, "reason") else exc)
    raise OpenAIServiceError(
      "Could not connect to OpenAI. Check backend internet access and try again."
    ) from exc
  except (json.JSONDecodeError, UnicodeDecodeError) as exc:
    logger.warning("OpenAI returned an unreadable response")
    raise OpenAIServiceError("OpenAI returned an invalid response. Please try again.") from exc

  text = _extract_text(body)
  if not text:
    logger.warning("OpenAI response contained no output text")
    raise OpenAIServiceError("OpenAI returned no text. Please try again.")
  return text
