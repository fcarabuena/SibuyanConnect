from datetime import timedelta

from django.shortcuts import render
from django.utils import timezone

from core.town import get_current_town

from .models import JeepneySchedule, Route, TricycleFare, Trip


def board(request):
    town = get_current_town(request)
    today = timezone.localdate()
    return render(request, "transport/board.html", {
        "trips": Trip.objects.for_town(town)
        .filter(departure_date__range=(today, today + timedelta(days=3)))
        .select_related("route", "route__municipality"),
        "routes": Route.objects.filter(is_active=True).for_town(town).select_related("municipality"),
        "jeepneys": JeepneySchedule.objects.for_town(town).select_related("origin", "destination"),
        "fares": TricycleFare.objects.for_town(town).select_related("municipality"),
        "today": today,
    })
