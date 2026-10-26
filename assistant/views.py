from django.conf import settings
from django.shortcuts import render
from django.utils.translation import get_language

from core.town import get_current_town

from . import engine
from .models import AssistantQuery


def chat(request):
    question = (request.POST.get("q") or request.GET.get("q") or "").strip()[:500]
    result = None
    if question:
        lang = get_language()
        result = engine.answer(question, lang, get_current_town(request))
        AssistantQuery.objects.create(question=question, language=lang, layer=result["layer"])
    template = "assistant/_reply.html" if request.headers.get("HX-Request") else "assistant/chat.html"
    return render(request, template, {
        "question": question,
        "result": result,
        "llm_enabled": settings.ASSISTANT_LLM_BACKEND in ("gemini", "ollama"),
    })
