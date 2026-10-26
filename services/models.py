from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from core.models import Municipality, Office, TimeStampedModel, TownQuerySet


class ServiceCategory(models.Model):
    name = models.CharField(max_length=80)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=4, blank=True, help_text=_("An emoji shown on the card"))
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name_plural = "service categories"

    def __str__(self):
        return self.name


class Service(TimeStampedModel):
    """A frontline service as described in the LGU's Citizen's Charter (RA 11032)."""

    municipality = models.ForeignKey(
        Municipality, on_delete=models.CASCADE, null=True, blank=True, related_name="services"
    )
    category = models.ForeignKey(ServiceCategory, on_delete=models.PROTECT, related_name="services")
    office = models.ForeignKey(Office, on_delete=models.SET_NULL, null=True, blank=True, related_name="services")
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=160)
    summary = models.TextField()
    who_may_apply = models.TextField(blank=True)
    fees = models.TextField(blank=True, help_text=_("Human-readable fee breakdown"))
    fee_amount = models.DecimalField(
        max_digits=9, decimal_places=2, null=True, blank=True, help_text=_("Base fee in PHP; empty if free/varies")
    )
    processing_time = models.CharField(max_length=120, blank=True)
    office_hours = models.CharField(max_length=120, blank=True, help_text=_("Leave empty to use the office's hours"))
    legal_basis = models.CharField(max_length=200, blank=True)
    is_published = models.BooleanField(default=True)
    view_count = models.PositiveIntegerField(default=0, editable=False)

    objects = TownQuerySet.as_manager()

    class Meta:
        ordering = ["category__order", "name"]
        unique_together = [("municipality", "slug")]

    def __str__(self):
        town = self.municipality.code if self.municipality else "ALL"
        return f"{self.name} [{town}]"

    def get_absolute_url(self):
        return reverse("services:detail", args=[self.pk, self.slug])

    @property
    def hours(self):
        return self.office_hours or (self.office.office_hours if self.office else "")

    def requirement_questions(self):
        """Distinct conditions that switch extra requirements on, for the checklist generator."""
        # Read through the model attribute so translation fallbacks apply.
        questions = []
        for req in self.requirements.all():
            if req.condition and req.condition not in questions:
                questions.append(req.condition)
        return questions


class ServiceStep(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="steps")
    order = models.PositiveSmallIntegerField(default=1)
    description = models.TextField()
    responsible = models.CharField(max_length=120, blank=True, help_text=_("Who does this step"))
    duration = models.CharField(max_length=60, blank=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"Step {self.order}"


class ServiceRequirement(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="requirements")
    order = models.PositiveSmallIntegerField(default=1)
    text = models.CharField(max_length=255)
    where_to_get = models.CharField(max_length=200, blank=True)
    condition = models.CharField(
        max_length=160, blank=True,
        help_text=_("Leave empty if always required. Otherwise a yes/no question, e.g. "
                    "'Is the registration late (more than 30 days)?'. Requirements sharing "
                    "the same question are grouped in the checklist generator."),
    )
    is_optional = models.BooleanField(default=False)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.text


class ServiceForm(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="forms")
    title = models.CharField(max_length=160)
    file = models.FileField(upload_to="forms/", blank=True)
    external_url = models.URLField(blank=True)

    def __str__(self):
        return self.title

    @property
    def url(self):
        return self.file.url if self.file else self.external_url
