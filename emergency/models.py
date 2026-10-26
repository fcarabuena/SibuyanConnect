from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import Barangay, Municipality, TownQuerySet


class Hotline(models.Model):
    class Agency(models.TextChoices):
        NATIONAL = "national", _("National emergency")
        MDRRMO = "mdrrmo", _("MDRRMO")
        PNP = "pnp", _("Police (PNP)")
        BFP = "bfp", _("Fire (BFP)")
        HOSPITAL = "hospital", _("Hospital")
        RHU = "rhu", _("Rural Health Unit")
        COAST_GUARD = "pcg", _("Coast Guard")
        POWER = "power", _("Power cooperative")
        OTHER = "other", _("Other")

    municipality = models.ForeignKey(
        Municipality, on_delete=models.CASCADE, null=True, blank=True, help_text=_("Empty = island-wide")
    )
    agency = models.CharField(max_length=10, choices=Agency.choices)
    name = models.CharField(max_length=120)
    number = models.CharField(max_length=40)
    alt_number = models.CharField(max_length=40, blank=True)
    is_24h = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)
    is_verified = models.BooleanField(
        default=False, help_text=_("Tick only after calling the number to confirm it works")
    )

    objects = TownQuerySet.as_manager()

    class Meta:
        ordering = ["order", "agency", "name"]

    def __str__(self):
        return f"{self.name}: {self.number}"

    @property
    def tel(self):
        return "".join(ch for ch in self.number if ch.isdigit() or ch == "+")


class EvacuationCenter(models.Model):
    barangay = models.ForeignKey(Barangay, on_delete=models.CASCADE, related_name="evacuation_centers")
    name = models.CharField(max_length=160)
    capacity = models.PositiveIntegerField(null=True, blank=True, help_text=_("Persons"))
    facilities = models.CharField(max_length=200, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        ordering = ["barangay__municipality__order", "barangay__name", "name"]

    def __str__(self):
        return f"{self.name} ({self.barangay})"


class PreparednessGuide(models.Model):
    class Hazard(models.TextChoices):
        TYPHOON = "typhoon", _("Typhoon")
        FLOOD = "flood", _("Flood")
        LANDSLIDE = "landslide", _("Landslide")
        EARTHQUAKE = "earthquake", _("Earthquake")
        STORM_SURGE = "surge", _("Storm surge")

    hazard = models.CharField(max_length=12, choices=Hazard.choices)
    title = models.CharField(max_length=160)
    body = models.TextField(help_text=_("One tip per line"))
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title

    def tips(self):
        return [line.strip("-* ").strip() for line in self.body.splitlines() if line.strip()]
