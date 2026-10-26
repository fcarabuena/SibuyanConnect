from django.db import models
from django.utils.translation import gettext_lazy as _

from core.images import compress_new_images
from core.models import Municipality, TimeStampedModel, TownQuerySet


class Attraction(TimeStampedModel):
    class Kind(models.TextChoices):
        MOUNTAIN = "mountain", _("Mountain / trail")
        FALLS = "falls", _("Waterfall")
        RIVER = "river", _("River")
        BEACH = "beach", _("Beach / coast")
        CULTURAL = "cultural", _("Cultural / heritage")
        VIEWPOINT = "viewpoint", _("Viewpoint")

    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, related_name="attractions")
    kind = models.CharField(max_length=10, choices=Kind.choices)
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120, unique=True)
    summary = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    tips = models.TextField(blank=True, help_text=_("One tip per line"))
    best_time = models.CharField(max_length=255, blank=True, help_text=_("Best time to visit"))
    getting_there = models.CharField(max_length=255, blank=True, help_text=_("How to get there"))
    guide_requirement = models.CharField(max_length=200, blank=True, help_text=_("e.g. Accredited local guide required"))
    environmental_fee = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    fee_notes = models.CharField(max_length=200, blank=True)
    is_protected_area = models.BooleanField(default=False)
    within_ancestral_domain = models.BooleanField(default=False)
    is_open = models.BooleanField(default=True)
    closure_note = models.CharField(max_length=200, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    cover = models.ImageField(upload_to="attractions/", blank=True)

    objects = TownQuerySet.as_manager()

    class Meta:
        ordering = ["municipality__order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        compress_new_images(self, "cover")
        super().save(*args, **kwargs)


class ClimbAdvisory(TimeStampedModel):
    """Trail status / permit info for Mt. Guiting-Guiting Natural Park, as issued by DENR-PAMO."""

    class Status(models.TextChoices):
        OPEN = "open", _("Open")
        RESTRICTED = "restricted", _("Restricted")
        CLOSED = "closed", _("Closed")

    attraction = models.ForeignKey(Attraction, on_delete=models.CASCADE, related_name="advisories")
    trail = models.CharField(max_length=120)
    status = models.CharField(max_length=10, choices=Status.choices)
    season_note = models.CharField(max_length=200, blank=True)
    permit_requirements = models.TextField(blank=True)
    valid_from = models.DateField()
    valid_until = models.DateField(null=True, blank=True)
    issued_by = models.CharField(max_length=120, default="DENR - Protected Area Management Office")
    source_url = models.URLField(blank=True)

    class Meta:
        ordering = ["-valid_from"]
        verbose_name_plural = "climb advisories"

    def __str__(self):
        return f"{self.trail}: {self.get_status_display()}"


class Business(TimeStampedModel):
    class Kind(models.TextChoices):
        ACCOMMODATION = "stay", _("Accommodation")
        RESTAURANT = "food", _("Restaurant / eatery")
        GUIDE = "guide", _("Tour guide")
        TRANSPORT = "transport", _("Transport operator")
        TOUR = "tour", _("Tour operator")

    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE)
    kind = models.CharField(max_length=10, choices=Kind.choices)
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    facebook_url = models.URLField(blank=True)
    is_accredited = models.BooleanField(default=False)
    accredited_by = models.CharField(max_length=60, blank=True, help_text=_("e.g. DOT, LGU Tourism Office"))
    accreditation_no = models.CharField(max_length=60, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    objects = TownQuerySet.as_manager()

    class Meta:
        ordering = ["kind", "name"]
        verbose_name_plural = "businesses"

    def __str__(self):
        return self.name


class TravelRule(models.Model):
    class Scope(models.TextChoices):
        GENERAL = "general", _("General")
        PROTECTED_AREA = "protected", _("Protected areas")
        ANCESTRAL_DOMAIN = "ancestral", _("Ancestral domain of the Sibuyan Mangyan Tagabukid")

    scope = models.CharField(max_length=10, choices=Scope.choices)
    title = models.CharField(max_length=160)
    body = models.TextField()
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["scope", "order"]

    def __str__(self):
        return self.title
