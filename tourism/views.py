from django.shortcuts import render

from core.town import get_current_town

from .models import Attraction, Business, TravelRule
from .showcase import attraction_photos


def attractions(request):
    town = get_current_town(request)
    places = Attraction.objects.select_related("municipality").prefetch_related("advisories")
    businesses = Business.objects.filter(is_accredited=True).select_related("municipality")
    if town:
        places = places.filter(municipality=town)
        businesses = businesses.filter(municipality=town)
    places = list(places)
    for place in places:
        place.photos = attraction_photos(place.slug)
    # Places with real photos first; placeholders after.
    places.sort(key=lambda p: p.photos["header"] is None)
    pins = [
        {"name": p.name, "town": p.municipality.name, "lat": float(p.latitude), "lon": float(p.longitude),
         "anchor": p.slug}
        for p in places if p.latitude is not None and p.longitude is not None
    ]
    return render(request, "tourism/attractions.html", {
        "attractions": places,
        "pins": pins,
        "businesses": businesses,
        "rules": TravelRule.objects.all(),
    })
