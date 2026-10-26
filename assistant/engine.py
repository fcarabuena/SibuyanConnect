"""Help assistant.

Layer 1 (always on, no network): keyword search over FAQ entries, services and
programs. Uses PostgreSQL full-text search in production and a simple keyword
score on SQLite.

Layer 2 (optional, off by default): a free-tier or self-hosted LLM answers
from the same site content when layer 1 finds nothing. If it is disabled or
fails, the assistant offers to open a concern ticket for a human to answer.
"""
import json
import logging
import re
import urllib.request
from functools import reduce
from operator import or_

from django.conf import settings
from django.db import connection

from core.search import multilingual_q
from programs.models import Program
from services.models import Service

from .models import FAQEntry

log = logging.getLogger(__name__)

STOP_WORDS = {
    # English
    "a", "an", "the", "how", "do", "does", "i", "me", "my", "to", "of", "for", "what", "where", "when",
    "is", "are", "can", "get", "in", "on", "and", "or", "it", "you", "please", "need", "want",
    # Filipino
    "ano", "paano", "saan", "kailan", "ang", "ng", "sa", "mga", "ko", "po", "ba", "na", "at", "ako",
    "kumuha", "makakuha", "gusto",
    # Romblomanon
    "diin", "kag", "kang", "ako", "ikaw", "baea", "ano", "pauno",
}
MIN_FAQ_SCORE = 2


def keywords(text):
    words = re.findall(r"[\w\-]+", text.lower())
    return [w for w in words if len(w) > 2 and w not in STOP_WORDS]


def _lang_fields(base, lang):
    fields = [f"{base}_{lang}"]
    if lang != "en":
        fields.append(f"{base}_en")  # people often mix English into Filipino questions
    return fields


def search_faq(question, lang, town=None):
    words = keywords(question)
    if not words:
        return None
    qs = FAQEntry.objects.filter(is_published=True).for_town(town)
    if connection.vendor == "postgresql":
        from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector

        vector = reduce(lambda a, b: a + b, [
            SearchVector(f, weight=w, config="simple")
            for base, w in (("question", "A"), ("keywords", "A"), ("answer", "B"))
            for f in _lang_fields(base, lang)
        ])
        query = reduce(or_, [SearchQuery(w, config="simple") for w in words])
        best = (
            qs.annotate(rank=SearchRank(vector, query)).filter(rank__gte=0.1).order_by("-rank").first()
        )
        return best

    # SQLite / development: score entries by keyword hits.
    best, best_score = None, 0
    for entry in qs:
        strong = " ".join(
            (getattr(entry, f) or "") for base in ("question", "keywords") for f in _lang_fields(base, lang)
        ).lower()
        weak = " ".join((getattr(entry, f) or "") for f in _lang_fields("answer", lang)).lower()
        score = sum(2 for w in words if w in strong) + sum(1 for w in words if w in weak)
        if score > best_score:
            best, best_score = entry, score
    return best if best_score >= MIN_FAQ_SCORE else None


def search_site(question, town=None, limit=3):
    words = keywords(question)
    if not words:
        return []
    cond = multilingual_q(["name", "summary"], words)
    results, seen = [], set()
    for model in (Service, Program):
        matches = model.objects.filter(is_published=True).for_town(town).filter(cond)[:limit * 3]
        for obj in matches:
            if obj.name in seen:  # each town has its own copy of a service; list it once
                continue
            seen.add(obj.name)
            results.append({"title": obj.name, "url": obj.get_absolute_url(), "summary": obj.summary})
    return results[:limit]


def _context_text(question, town):
    snippets = [f"Q: {f.question}\nA: {f.answer}" for f in FAQEntry.objects.filter(is_published=True)[:40]]
    snippets += [f"Service: {s.name} - {s.summary}" for s in Service.objects.for_town(town)[:30]]
    return "\n\n".join(snippets)[:12000]


def ask_llm(question, lang, town=None):
    backend = settings.ASSISTANT_LLM_BACKEND
    if backend not in ("gemini", "ollama"):
        return None
    language = dict(settings.LANGUAGES).get(lang, "English")
    prompt = (
        "You are the help assistant of SibuyanConnect, the community portal of the LGUs of "
        "Magdiwang, San Fernando and Cajidiocan on Sibuyan Island, Romblon, Philippines. "
        "Answer ONLY using the context below. If the answer is not in the context, reply with "
        f"exactly NO_ANSWER. Reply in {language}, in 2-4 short sentences.\n\n"
        f"CONTEXT:\n{_context_text(question, town)}\n\nQUESTION: {question}"
    )
    try:
        if backend == "gemini":
            if not settings.GEMINI_API_KEY:
                return None
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            headers = {"Content-Type": "application/json", "x-goog-api-key": settings.GEMINI_API_KEY}
            data = _post_json(url, payload, headers)
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            url = settings.OLLAMA_URL.rstrip("/") + "/api/generate"
            data = _post_json(url, {"model": settings.OLLAMA_MODEL, "prompt": prompt, "stream": False},
                              {"Content-Type": "application/json"})
            text = data["response"]
    except Exception:
        log.exception("LLM backend %s failed", backend)
        return None
    text = text.strip()
    return None if not text or "NO_ANSWER" in text else text


def _post_json(url, payload, headers, timeout=20):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def answer(question, lang, town=None):
    """Return a dict: layer, answer, link, links, handoff."""
    faq = search_faq(question, lang, town)
    links = search_site(question, town)
    if faq:
        return {"layer": "faq", "answer": faq.answer, "link": faq.link_url, "links": links, "handoff": False}
    if links:
        return {"layer": "site", "answer": None, "link": "", "links": links, "handoff": False}
    llm = ask_llm(question, lang, town)
    if llm:
        return {"layer": "llm", "answer": llm, "link": "", "links": [], "handoff": False}
    return {"layer": "none", "answer": None, "link": "", "links": [], "handoff": True}
