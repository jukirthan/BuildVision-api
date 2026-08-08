"""Server-side adapter for Google's Gemini generateContent REST API."""

import json
import logging
import os
import urllib.error
import urllib.request
from urllib.parse import quote


logger = logging.getLogger(__name__)


class GeminiServiceError(Exception):
  """An expected Gemini configuration/provider failure safe for the client."""


def _provider_error(status):
  if status in (401, 403):
    return "Gemini authentication failed. Set a valid GEMINI_API_KEY on the Flask backend."
  if status == 429:
    return "Gemini rate limit reached. Please wait a moment and try again."
  if status >= 500:
    return "Gemini is temporarily unavailable. Please try again shortly."
  return "Gemini rejected the chat request. Check the backend model configuration."


def _extract_text(body):
  chunks = []
  for candidate in body.get("candidates", []) or []:
    content = candidate.get("content", {}) or {}
    for part in content.get("parts", []) or []:
      text = part.get("text")
      if isinstance(text, str) and text.strip():
        chunks.append(text)
  return "\n".join(chunks).strip()


def generate_chat_reply(messages, system_prompt):
  api_key = os.getenv("GEMINI_API_KEY", "").strip()
  if not api_key:
    raise GeminiServiceError(
      "Gemini is not configured. Add GEMINI_API_KEY to the Flask backend environment."
    )

  model = os.getenv("GEMINI_MODEL", "gemini-flash-latest").strip() or "gemini-flash-latest"
  contents = [
    {
      "role": "model" if message["role"] == "assistant" else "user",
      "parts": [{"text": message["content"]}],
    }
    for message in messages
  ]
  body = json.dumps(
    {
      "system_instruction": {"parts": [{"text": system_prompt}]},
      "contents": contents,
      "generationConfig": {"maxOutputTokens": 800},
    }
  ).encode("utf-8")
  url = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{quote(model, safe='')}:generateContent"
  )
  request = urllib.request.Request(
    url,
    data=body,
    headers={
      "Content-Type": "application/json",
      "x-goog-api-key": api_key,
    },
    method="POST",
  )

  try:
    with urllib.request.urlopen(request, timeout=35) as response:
      response_body = json.loads(response.read().decode("utf-8"))
  except urllib.error.HTTPError as exc:
    logger.warning("Gemini generateContent returned HTTP %s", exc.code)
    raise GeminiServiceError(_provider_error(exc.code)) from exc
  except (urllib.error.URLError, TimeoutError) as exc:
    logger.warning("Gemini connection failed: %s", exc.reason if hasattr(exc, "reason") else exc)
    raise GeminiServiceError(
      "Could not connect to Gemini. Check backend internet access and try again."
    ) from exc
  except (json.JSONDecodeError, UnicodeDecodeError) as exc:
    logger.warning("Gemini returned an unreadable response")
    raise GeminiServiceError("Gemini returned an invalid response. Please try again.") from exc

  text = _extract_text(response_body)
  if not text:
    logger.warning("Gemini response contained no output text")
    raise GeminiServiceError("Gemini returned no text. The request may have been blocked.")
  return text
