from django.shortcuts import render

from core.models import Office
from core.town import get_current_town

from .models import Official, PublicDocument


def transparency(request):
    town = get_current_town(request)
    documents = PublicDocument.objects.for_town(town).select_related("municipality")
    kind = request.GET.get("kind")
    if kind in PublicDocument.Kind.values:
        documents = documents.filter(kind=kind)
    offices = Office.objects.select_related("municipality")
    if town:
        offices = offices.filter(municipality=town)
    return render(request, "civic/transparency.html", {
        "documents": documents,
        "kinds": PublicDocument.Kind.choices,
        "active_kind": kind,
        "officials": Official.objects.for_town(town).select_related("municipality"),
        "offices": offices,
    })
