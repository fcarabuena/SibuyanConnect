from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.images import compress_new_images
from core.models import Municipality, Office, TimeStampedModel, TownQuerySet


class PublicDocument(TimeStampedModel):
    """Transparency Corner: ordinances, EOs, budget, procurement, Citizen's Charter."""

    class Kind(models.TextChoices):
        ORDINANCE = "ordinance", _("Ordinance")
        RESOLUTION = "resolution", _("Resolution")
        EXECUTIVE_ORDER = "eo", _("Executive order")
        BUDGET = "budget", _("Budget / financial report")
        PROCUREMENT = "procurement", _("Procurement notice")
        CHARTER = "charter", _("Citizen's Charter")
        REPORT = "report", _("Report")

    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, null=True, blank=True)
    kind = models.CharField(max_length=12, choices=Kind.choices)
    number = models.CharField(max_length=60, blank=True, help_text=_("e.g. Ord. No. 2026-04"))
    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True)
    date_issued = models.DateField()
    file = models.FileField(upload_to="documents/%Y/", blank=True)
    external_url = models.URLField(blank=True)

    objects = TownQuerySet.as_manager()

    class Meta:
        ordering = ["-date_issued"]

    def __str__(self):
        return f"{self.number} {self.title}".strip()


class Official(models.Model):
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, related_name="officials")
    name = models.CharField(max_length=120)
    position = models.CharField(max_length=120)
    office = models.ForeignKey(Office, on_delete=models.SET_NULL, null=True, blank=True)
    term = models.CharField(max_length=20, blank=True, help_text=_("e.g. 2025-2028"))
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    objects = TownQuerySet.as_manager()

    class Meta:
        ordering = ["municipality__order", "order"]

    def __str__(self):
        return f"{self.position} {self.name}"


class EnvironmentUpdate(TimeStampedModel):
    """Environment Watch. Editors should keep these factual, sourced and neutral."""

    class Kind(models.TextChoices):
        PROTECTED_AREA = "protected", _("Protected area update")
        CONSERVATION = "conservation", _("Conservation program")
        CLEANUP = "cleanup", _("Coastal / river clean-up")
        REPORT = "report", _("Environmental report")

    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, null=True, blank=True)
    kind = models.CharField(max_length=12, choices=Kind.choices)
    title = models.CharField(max_length=200)
    body = models.TextField()
    source = models.CharField(max_length=200, help_text=_("Who issued the information, e.g. DENR-PAMO, MENRO"))
    source_url = models.URLField(blank=True)
    image = models.ImageField(upload_to="environment/", blank=True)
    published_at = models.DateTimeField(default=timezone.now)

    objects = TownQuerySet.as_manager()

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        compress_new_images(self, "image")
        super().save(*args, **kwargs)
