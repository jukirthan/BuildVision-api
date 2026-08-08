import os

from flask import request

from app.services.gemini_service import GeminiServiceError, generate_chat_reply as generate_gemini_reply
from app.services.openai_service import SYSTEM_PROMPT, OpenAIServiceError, generate_chat_reply
from app.utils import error_response, success_response


class AiController:
  @staticmethod
  def chat():
    data = request.get_json(silent=True) or {}
    raw_messages = data.get("messages")
    if not isinstance(raw_messages, list) or not raw_messages:
      return error_response("Send at least one chat message.", 400)
    if len(raw_messages) > 24:
      return error_response("This conversation is too long. Start a new chat.", 400)

    messages = []
    for item in raw_messages:
      if not isinstance(item, dict) or item.get("role") not in {"user", "assistant"}:
        return error_response("Chat messages have an invalid role.", 400)
      content = item.get("content")
      if not isinstance(content, str) or not content.strip():
        return error_response("Chat messages cannot be empty.", 400)
      if len(content) > 4000:
        return error_response("A chat message is too long.", 400)
      messages.append({"role": item["role"], "content": content.strip()})

    if messages[-1]["role"] != "user":
      return error_response("The latest chat message must come from the user.", 400)

    provider = str(data.get("provider") or os.getenv("AI_PROVIDER", "openai")).strip().lower()
    if provider not in {"openai", "gemini"}:
      return error_response("Unsupported AI provider. Choose OpenAI or Gemini.", 400)

    try:
      if provider == "gemini":
        text = generate_gemini_reply(messages, system_prompt=SYSTEM_PROMPT)
      else:
        text = generate_chat_reply(messages)
    except (OpenAIServiceError, GeminiServiceError) as exc:
      return error_response(str(exc), 503)
    except Exception:
      # Do not leak provider/network details into the browser.
      return error_response("The AI assistant is temporarily unavailable.", 503)

    return success_response({"text": text, "provider": provider}, "AI response ready")
