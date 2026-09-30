import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .models import ChatSession, ChatMessage
from .services import run_agent_turn


@login_required
def chat_page_view(request):
    return render(request, "ai_agent/chat.html")


@login_required
@require_POST
def chat_message_view(request):
    """Async fetch endpoint used by static/js/agent_chat.js."""
    try:
        payload = json.loads(request.body)
        user_message = payload["message"].strip()
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({"error": "Malformed request body."}, status=400)

    if not user_message:
        return JsonResponse({"error": "Message cannot be empty."}, status=400)

    session_id = payload.get("session_id")
    if session_id:
        session, _ = ChatSession.objects.get_or_create(pk=session_id, user=request.user)
    else:
        session = ChatSession.objects.create(user=request.user)

    # Rebuild conversation history in Anthropic message format
    history = [
        {"role": m.role, "content": m.content}
        for m in session.messages.filter(role__in=["user", "assistant"])
    ]

    ChatMessage.objects.create(session=session, role="user", content=user_message)

    result = run_agent_turn(request.user, history, user_message)

    ChatMessage.objects.create(session=session, role="assistant", content=result["reply"])

    return JsonResponse({
        "session_id": session.id,
        "reply": result["reply"],
        "tool_trace": result["tool_trace"],
    })
