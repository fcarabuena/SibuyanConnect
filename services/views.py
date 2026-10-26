from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render

from core.search import multilingual_q
from core.town import get_current_town

from .models import Service, ServiceCategory


def service_list(request):
    town = get_current_town(request)
    services = Service.objects.filter(is_published=True).for_town(town).select_related(
        "category", "municipality", "office"
    )
    q = request.GET.get("q", "").strip()
    if q:
        for word in q.split()[:6]:  # every word must match, in any language
            services = services.filter(multilingual_q(["name", "summary"], word))
    category = request.GET.get("category")
    if category:
        services = services.filter(category__slug=category)
    return render(request, "services/list.html", {
        "services": services,
        "categories": ServiceCategory.objects.all(),
        "q": q,
        "active_category": category,
    })


def service_detail(request, pk, slug):
    service = get_object_or_404(
        Service.objects.select_related("office", "municipality", "category"), pk=pk, is_published=True
    )
    if service.slug != slug:
        return redirect(service, permanent=True)
    # Cheap first-party analytics: count views for the "most-viewed services" report.
    Service.objects.filter(pk=pk).update(view_count=F("view_count") + 1)
    return render(request, "services/detail.html", {
        "service": service,
        "questions": service.requirement_questions(),
    })


def checklist(request, pk):
    """'What do I need?' - build a personalised checklist from the user's yes/no answers."""
    service = get_object_or_404(Service, pk=pk, is_published=True)
    questions = service.requirement_questions()
    answered_yes = [q for i, q in enumerate(questions) if request.GET.get(f"q{i}") == "yes"]
    items = [
        r for r in service.requirements.all()
        if not r.condition or r.condition in answered_yes
    ]
    template = "services/_checklist.html" if request.headers.get("HX-Request") else "services/checklist.html"
    return render(request, template, {
        "service": service,
        "items": items,
        "answered_yes": answered_yes,
    })
