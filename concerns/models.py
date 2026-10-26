import secrets

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models import Barangay, Municipality, Office, TimeStampedModel

PRIVACY_NOTICE_VERSION = "2026-10"


class ConcernCategory(models.Model):
    """Each category is routed to one kind of office in the citizen's municipality."""

    name = models.CharField(max_length=80)
    slug = models.SlugField(unique=True)
    description = models.CharField(max_length=200, blank=True)
    icon = models.CharField(max_length=4, blank=True)
    office_kind = models.CharField(max_length=20, choices=Office.Kind.choices)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name_plural = "concern categories"

    def __str__(self):
        return self.name


def _token():
    return secrets.token_urlsafe(16)


class Concern(TimeStampedModel):
    class Status(models.TextChoices):
        RECEIVED = "received", _("Received")
        ASSIGNED = "assigned", _("Assigned")
        IN_PROGRESS = "in_progress", _("In progress")
        RESOLVED = "resolved", _("Resolved")

    class Priority(models.TextChoices):
        NORMAL = "normal", _("Normal")
        HIGH = "high", _("High")
        URGENT = "urgent", _("Urgent")

    TRACKER_STEPS = [Status.RECEIVED, Status.ASSIGNED, Status.IN_PROGRESS, Status.RESOLVED]

    ticket_number = models.CharField(max_length=24, unique=True, blank=True, editable=False)
    access_token = models.CharField(max_length=32, default=_token, editable=False)
    municipality = models.ForeignKey(Municipality, on_delete=models.PROTECT, related_name="concerns")
    barangay = models.ForeignKey(Barangay, on_delete=models.PROTECT)
    category = models.ForeignKey(ConcernCategory, on_delete=models.PROTECT)
    office = models.ForeignKey(
        Office, on_delete=models.SET_NULL, null=True, blank=True, related_name="concerns",
        help_text=_("Set automatically from the category; staff may re-route."),
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="assigned_concerns", limit_choices_to={"is_staff": True},
    )
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.RECEIVED)
    priority = models.CharField(max_length=8, choices=Priority.choices, default=Priority.NORMAL)
    subject = models.CharField(max_length=140)
    description = models.TextField()
    location_detail = models.CharField(max_length=200, blank=True, help_text=_("Landmark, purok or street"))
    photo = models.ImageField(upload_to="concerns/%Y/%m/", blank=True)

    # Contact details: personal data under RA 10173 - visible only to assigned staff.
    citizen = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="concerns"
    )
    name = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    consent_given_at = models.DateTimeField()
    privacy_notice_version = models.CharField(max_length=10, default=PRIVACY_NOTICE_VERSION)
    source = models.CharField(max_length=12, default="web", help_text=_("web or assistant"))

    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.ticket_number} - {self.subject}"

    def save(self, *args, **kwargs):
        if self.office_id is None and self.category_id and self.municipality_id:
            self.office = Office.objects.filter(
                municipality_id=self.municipality_id, kind=self.category.office_kind
            ).first() or Office.objects.filter(
                municipality_id=self.municipality_id, kind=Office.Kind.MAYOR
            ).first()
        if self.status == self.Status.RESOLVED and self.resolved_at is None:
            self.resolved_at = timezone.now()
        elif self.status != self.Status.RESOLVED:
            self.resolved_at = None
        super().save(*args, **kwargs)
        if not self.ticket_number:
            # e.g. SC-MAG-2026-00042: readable over the phone, unique via the pk.
            year = timezone.localtime(self.created_at).year
            self.ticket_number = f"SC-{self.municipality.code}-{year}-{self.pk:05d}"
            super().save(update_fields=["ticket_number"])

    def get_absolute_url(self):
        return reverse("concerns:ticket", args=[self.ticket_number, self.access_token])

    def tracker(self):
        """Steps for the status tracker with done/current flags."""
        current = self.TRACKER_STEPS.index(self.status)
        return [
            {"label": step.label, "done": i < current, "current": i == current}
            for i, step in enumerate(self.TRACKER_STEPS)
        ]

    @property
    def resolution_hours(self):
        if self.resolved_at:
            return round((self.resolved_at - self.created_at).total_seconds() / 3600, 1)
        return None


class ConcernMessage(models.Model):
    class Sender(models.TextChoices):
        CITIZEN = "citizen", _("Citizen")
        STAFF = "staff", _("LGU staff")
        SYSTEM = "system", _("System")

    concern = models.ForeignKey(Concern, on_delete=models.CASCADE, related_name="messages")
    sender = models.CharField(max_length=8, choices=Sender.choices, default=Sender.STAFF)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    body = models.TextField()
    is_internal = models.BooleanField(default=False, help_text=_("Internal note: hidden from the citizen"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.get_sender_display()} on {self.concern.ticket_number}"


class StatusChange(models.Model):
    """Audit trail of status changes, also used for resolution-time analytics."""

    concern = models.ForeignKey(Concern, on_delete=models.CASCADE, related_name="status_changes")
    from_status = models.CharField(max_length=12, choices=Concern.Status.choices, blank=True)
    to_status = models.CharField(max_length=12, choices=Concern.Status.choices)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
