from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from core.models import Municipality, TownQuerySet


class Route(models.Model):
    """A ferry route to/from a Sibuyan port. Times are in schedule_text; daily status lives in Trip."""

    municipality = models.ForeignKey(
        Municipality, on_delete=models.CASCADE, help_text=_("Town of the Sibuyan port")
    )
    port = models.CharField(max_length=120, help_text=_("Sibuyan-side port"))
    origin = models.CharField(max_length=80)
    destination = models.CharField(max_length=80)
    operator = models.CharField(max_length=120)
    vessel = models.CharField(max_length=120, blank=True)
    schedule_text = models.CharField(max_length=200, help_text=_("e.g. Mon/Wed/Fri, depart 10:00 PM"))
    duration = models.CharField(max_length=60, blank=True)
    fare_info = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    objects = TownQuerySet.as_manager()

    class Meta:
        ordering = ["municipality__order", "origin", "destination"]

    def __str__(self):
        return f"{self.origin} → {self.destination} ({self.operator})"


class TripQuerySet(models.QuerySet):
    def for_town(self, town):
        return self if town is None else self.filter(route__municipality=town)


class Trip(models.Model):
    """One dated sailing, whose status port/LGU staff update from the admin."""

    class Status(models.TextChoices):
        ON_TIME = "on_time", _("On time")
        DELAYED = "delayed", _("Delayed")
        CANCELLED = "cancelled", _("Cancelled")
        DEPARTED = "departed", _("Departed")

    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="trips")
    departure_date = models.DateField()
    departure_time = models.TimeField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ON_TIME)
    status_note = models.CharField(max_length=200, blank=True, help_text=_("e.g. 'No sailing: Signal No. 2'"))
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    objects = TripQuerySet.as_manager()

    class Meta:
        ordering = ["departure_date", "departure_time"]

    def __str__(self):
        return f"{self.route} {self.departure_date} {self.departure_time:%H:%M}"


class JeepneyQuerySet(models.QuerySet):
    def for_town(self, town):
        return self if town is None else self.filter(Q(origin=town) | Q(destination=town))


class JeepneySchedule(models.Model):
    origin = models.ForeignKey(Municipality, on_delete=models.CASCADE, related_name="jeepney_departures")
    destination = models.ForeignKey(Municipality, on_delete=models.CASCADE, related_name="jeepney_arrivals")
    terminal = models.CharField(max_length=120)
    departure_time = models.TimeField()
    days = models.CharField(max_length=60, default="Daily")
    fare = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    notes = models.CharField(max_length=200, blank=True)

    objects = JeepneyQuerySet.as_manager()

    class Meta:
        ordering = ["origin__order", "departure_time"]

    def __str__(self):
        return f"{self.origin} → {self.destination} {self.departure_time:%H:%M}"


class TricycleFare(models.Model):
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE)
    from_point = models.CharField(max_length=120)
    to_point = models.CharField(max_length=120)
    regular_fare = models.DecimalField(max_digits=7, decimal_places=2)
    discounted_fare = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True,
        help_text=_("Student / senior / PWD fare"),
    )
    special_trip_fare = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    ordinance = models.CharField(max_length=120, blank=True, help_text=_("Fare ordinance reference"))

    objects = TownQuerySet.as_manager()

    class Meta:
        ordering = ["municipality__order", "from_point", "to_point"]

    def __str__(self):
        return f"{self.from_point} → {self.to_point}"
