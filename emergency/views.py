from django.shortcuts import render

from core.town import get_current_town

from .models import EvacuationCenter, Hotline, PreparednessGuide


def hub(request):
    town = get_current_town(request)
    centers = EvacuationCenter.objects.select_related("barangay", "barangay__municipality")
    if town:
        centers = centers.filter(barangay__municipality=town)
    return render(request, "emergency/hub.html", {
        "hotlines": Hotline.objects.for_town(town).select_related("municipality"),
        "centers": centers,
        "guides": PreparednessGuide.objects.all(),
    })
