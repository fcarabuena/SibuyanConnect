from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TownQuerySet(models.QuerySet):
    """Content tied to a municipality, or island-wide when municipality is empty."""

    def for_town(self, town):
        if town is None:
            return self
        return self.filter(Q(municipality=town) | Q(municipality__isnull=True))


class Municipality(models.Model):
    name = models.CharField(max_length=80)
    slug = models.SlugField(unique=True)
    code = models.CharField(max_length=3, unique=True, help_text=_("Used in ticket numbers, e.g. MAG"))
    tagline = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name_plural = "municipalities"

    def __str__(self):
        return self.name


class Barangay(models.Model):
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, related_name="barangays")
    name = models.CharField(max_length=80)

    class Meta:
        ordering = ["municipality__order", "name"]
        unique_together = [("municipality", "name")]

    def __str__(self):
        return f"{self.name}, {self.municipality.name}"


class Office(models.Model):
    """An LGU office. Concerns and services are routed to offices."""

    class Kind(models.TextChoices):
        MAYOR = "MAYOR", _("Mayor's Office")
        MDRRMO = "MDRRMO", _("MDRRMO (Disaster Risk Reduction)")
        MSWDO = "MSWDO", _("MSWDO (Social Welfare)")
        MENRO = "MENRO", _("MENRO (Environment)")
        ENGINEERING = "ENGINEERING", _("Municipal Engineering")
        HEALTH = "HEALTH", _("Municipal Health Office / RHU")
        AGRICULTURE = "AGRICULTURE", _("Municipal Agriculture Office")
        CIVIL_REGISTRY = "MCR", _("Municipal Civil Registrar")
        TREASURY = "TREASURY", _("Municipal Treasurer")
        BPLO = "BPLO", _("Business Permits and Licensing")
        TOURISM = "TOURISM", _("Tourism Office")
        OSCA = "OSCA", _("Office of Senior Citizens Affairs")
        PDAO = "PDAO", _("Persons with Disability Affairs Office")

    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, related_name="offices")
    kind = models.CharField(max_length=20, choices=Kind.choices)
    name = models.CharField(max_length=120)
    head = models.CharField(max_length=120, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    location = models.CharField(max_length=200, blank=True)
    office_hours = models.CharField(max_length=120, default="Mon-Fri, 8:00 AM - 5:00 PM")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        ordering = ["municipality__order", "name"]
        unique_together = [("municipality", "kind")]

    def __str__(self):
        return f"{self.name} ({self.municipality.code})"


class StaffProfile(models.Model):
    """Scopes a staff account. Permissions come from Django groups (see setup_roles)."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="staff_profile")
    municipality = models.ForeignKey(
        Municipality, on_delete=models.SET_NULL, null=True, blank=True,
        help_text=_("Leave empty for island-wide (Super Admin) staff."),
    )
    office = models.ForeignKey(
        Office, on_delete=models.SET_NULL, null=True, blank=True,
        help_text=_("Department staff only see concerns assigned to this office."),
    )
    position = models.CharField(max_length=120, blank=True)

    def __str__(self):
        return f"{self.user.get_username()} - {self.municipality or 'Island-wide'}"


class AlertQuerySet(TownQuerySet):
    def live(self):
        now = timezone.now()
        return self.filter(is_active=True, starts_at__lte=now).filter(
            Q(ends_at__isnull=True) | Q(ends_at__gte=now)
        )


class Alert(TimeStampedModel):
    class Kind(models.TextChoices):
        TYPHOON = "typhoon", _("Typhoon / weather")
        FERRY = "ferry", _("Ferry / sea travel")
        POWER = "power", _("Power interruption")
        WATER = "water", _("Water interruption")
        ROAD = "road", _("Road closure")
        HEALTH = "health", _("Health advisory")
        OTHER = "other", _("Other")

    class Level(models.TextChoices):
        INFO = "info", _("Information")
        WARNING = "warning", _("Warning")
        DANGER = "danger", _("Danger")

    municipality = models.ForeignKey(
        Municipality, on_delete=models.CASCADE, null=True, blank=True, help_text=_("Empty = island-wide")
    )
    kind = models.CharField(max_length=10, choices=Kind.choices)
    level = models.CharField(max_length=10, choices=Level.choices, default=Level.WARNING)
    title = models.CharField(max_length=160)
    body = models.TextField(blank=True)
    source_url = models.URLField(blank=True, help_text=_("Link to the official bulletin, e.g. PAGASA"))
    starts_at = models.DateTimeField(default=timezone.now)
    ends_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notify_subscribers = models.BooleanField(
        default=False, help_text=_("Email this alert to subscribers when saved")
    )

    objects = AlertQuerySet.as_manager()

    class Meta:
        ordering = ["-level", "-starts_at"]

    def __str__(self):
        return self.title


class AlertSubscription(TimeStampedModel):
    """Email subscription to alerts (Data Privacy Act: explicit opt-in, easy opt-out)."""

    email = models.EmailField()
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, null=True, blank=True)
    consent_given_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.email
