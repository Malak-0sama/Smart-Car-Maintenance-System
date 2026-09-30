"""Gemini-backed agent orchestration service.

Uses Google's Gemini Developer API directly over HTTPS so the project does not
need the Anthropic SDK. The selected Gemini Flash model has a Free Tier (subject
to Google's current usage limits).
"""
import json
import logging
from urllib import error, request

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError

from .prompts import SYSTEM_PERSONA, OUTPUT_FORMAT_INSTRUCTIONS
from .tools import TOOL_SCHEMAS, TOOL_FUNCTIONS

logger = logging.getLogger(__name__)

MAX_TOOL_ITERATIONS = 5
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _execute_tool(name: str, tool_input: dict, user) -> dict:
    func = TOOL_FUNCTIONS.get(name)
    if func is None:
        return {"error": f"Unknown tool '{name}'."}
    try:
        return func(user=user, **tool_input)
    except PermissionDenied as e:
        return {"error": f"Permission denied: {e}"}
    except ValidationError as e:
        return {"error": f"Invalid input: {e}"}
    except TypeError as e:
        return {"error": f"Invalid arguments for tool '{name}': {e}"}
    except Exception:
        logger.exception("Tool execution failed: %s", name)
        return {"error": "Internal error executing tool. Please try again."}


def _gemini_tool_declarations():
    """Translate the Anthropic-style registry into Gemini REST declarations."""
    return [
        {
            "name": schema["name"],
            "description": schema["description"],
            "parameters": schema["input_schema"],
        }
        for schema in TOOL_SCHEMAS
    ]


def _history_to_gemini_contents(conversation_history: list[dict], user_message: str):
    contents = []
    for item in conversation_history:
        role = "model" if item.get("role") == "assistant" else "user"
        content = item.get("content", "")
        if content:
            contents.append({"role": role, "parts": [{"text": content}]})
    contents.append({"role": "user", "parts": [{"text": user_message}]})
    return contents


def _generate(api_key: str, model: str, system_prompt: str, contents: list[dict]) -> dict:
    url = GEMINI_API_URL.format(model=model)
    body = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": contents,
        "tools": [{"function_declarations": _gemini_tool_declarations()}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1024},
    }
    req = request.Request(
        f"{url}?key={api_key}",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(raw).get("error", {}).get("message", raw)
        except json.JSONDecodeError:
            detail = raw
        logger.error("Gemini API error %s: %s", exc.code, detail)
        raise RuntimeError(f"Gemini API error ({exc.code}): {detail}") from exc
    except error.URLError as exc:
        logger.exception("Could not connect to Gemini")
        raise RuntimeError("Could not connect to Gemini. Check your internet connection.") from exc


def _extract_parts(response: dict):
    candidates = response.get("candidates") or []
    if not candidates:
        raise RuntimeError("Gemini returned no candidates.")
    return candidates[0].get("content", {}).get("parts", [])


def run_agent_turn(user, conversation_history: list[dict], user_message: str) -> dict:
    """Run one agent turn using Gemini function calling."""
    api_key = getattr(settings, "GEMINI_API_KEY", "")
    model = getattr(settings, "AI_MODEL", "gemini-2.5-flash")

    if not api_key:
        return {
            "reply": "AI is not configured yet. Add GEMINI_API_KEY to your .env file and restart the server.",
            "tool_trace": [],
        }

    app_context = _build_app_context(user)
    system_prompt = f"{SYSTEM_PERSONA}\n\n{OUTPUT_FORMAT_INSTRUCTIONS}\n\nCURRENT APP CONTEXT:\n{app_context}"
    contents = _history_to_gemini_contents(conversation_history, user_message)
    tool_trace = []

    for _ in range(MAX_TOOL_ITERATIONS):
        try:
            response = _generate(api_key, model, system_prompt, contents)
        except RuntimeError as exc:
            logger.exception("Gemini turn failed")
            return {"reply": str(exc), "tool_trace": tool_trace}

        parts = _extract_parts(response)
        function_calls = [p.get("functionCall") for p in parts if p.get("functionCall")]

        if not function_calls:
            text = "".join(p.get("text", "") for p in parts if p.get("text"))
            return {"reply": text or "I couldn't generate a response. Please try again.", "tool_trace": tool_trace}

        # Preserve the model's function-call message exactly as returned.
        contents.append({"role": "model", "parts": parts})
        function_response_parts = []

        for call in function_calls:
            name = call.get("name", "")
            args = call.get("args") or {}
            output = _execute_tool(name, args, user)
            tool_trace.append({"tool": name, "input": args, "output": output})
            function_response_parts.append({
                "functionResponse": {
                    "name": name,
                    "response": output,
                }
            })

        contents.append({"role": "user", "parts": function_response_parts})

    return {
        "reply": "I ran into trouble completing that request. Could you rephrase or simplify it?",
        "tool_trace": tool_trace,
    }


def _build_app_context(user) -> str:
    if user.is_customer():
        vehicles = user.vehicles.all()
        vehicle_lines = "\n".join(
            f"- id={v.id}: {v.year} {v.make} {v.model}, plate {v.license_plate}, "
            f"mileage {v.current_mileage_km} km"
            for v in vehicles
        ) or "  (no vehicles registered yet)"
        return f"User role: CUSTOMER\nUser's vehicles:\n{vehicle_lines}"

    return f"User role: {user.role}. This user does not own vehicles directly."
