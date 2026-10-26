from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models import Municipality, Office, TimeStampedModel, TownQuerySet

# Profile flags asked by the eligibility checker. Each maps to a requires_<key> field.
PROFILE_FLAGS = [
    ("student", _("I am a student (or will enrol this school year)")),
    ("farmer", _("I am a farmer (or farm worker)")),
    ("fisherfolk", _("I am a fisherfolk")),
    ("pwd", _("I am a person with disability")),
    ("solo_parent", _("I am a solo parent")),
    ("indigenous", _("I belong to an indigenous people (e.g. Sibuyan Mangyan Tagabukid)")),
    ("informal_worker", _("I am unemployed, underemployed or an informal worker")),
    ("in_crisis", _("My family faces a crisis now (illness, death, disaster, fire)")),
    ("listahanan_poor", _("Our household is listed as poor by DSWD (Listahanan)")),
]


class Program(TimeStampedModel):
    class Level(models.TextChoices):
        MUNICIPAL = "municipal", _("Municipal")
        PROVINCIAL = "provincial", _("Provincial (Romblon)")
        NATIONAL = "national", _("National")

    class Kind(models.TextChoices):
        SCHOLARSHIP = "scholarship", _("Scholarship / education")
        LIVELIHOOD = "livelihood", _("Livelihood / employment")
        CASH = "cash", _("Cash / social assistance")
        SENIOR_PWD = "senior_pwd", _("Senior citizen & PWD")
        AGRI = "agri", _("Farmer & fisherfolk support")
        HEALTH = "health", _("Health")

    municipality = models.ForeignKey(
        Municipality, on_delete=models.CASCADE, null=True, blank=True,
        help_text=_("Empty = available in all three towns"),
    )
    level = models.CharField(max_length=12, choices=Level.choices)
    kind = models.CharField(max_length=12, choices=Kind.choices)
    agency = models.CharField(max_length=120, help_text=_("e.g. DSWD, DOLE, CHED, DA, BFAR, LGU"))
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=160)
    summary = models.TextField()
    benefits = models.TextField(blank=True)
    how_to_apply = models.TextField(blank=True)
    contact_office = models.ForeignKey(Office, on_delete=models.SET_NULL, null=True, blank=True)
    official_url = models.URLField(blank=True)
    is_published = models.BooleanField(default=True)
    view_count = models.PositiveIntegerField(default=0, editable=False)

    # --- Eligibility rules (all set rules must pass) ---
    min_age = models.PositiveSmallIntegerField(null=True, blank=True)
    max_age = models.PositiveSmallIntegerField(null=True, blank=True)
    max_monthly_income = models.PositiveIntegerField(
        null=True, blank=True, help_text=_("Max household monthly income in PHP")
    )
    requires_student = models.BooleanField(default=False)
    requires_farmer = models.BooleanField(default=False)
    requires_fisherfolk = models.BooleanField(default=False)
    requires_farmer_or_fisherfolk = models.BooleanField(default=False)
    requires_pwd = models.BooleanField(default=False)
    requires_solo_parent = models.BooleanField(default=False)
    requires_indigenous = models.BooleanField(default=False)
    requires_informal_worker = models.BooleanField(default=False)
    requires_in_crisis = models.BooleanField(default=False)
    requires_listahanan_poor = models.BooleanField(default=False)
    eligibility_notes = models.TextField(blank=True, help_text=_("Other conditions the checker cannot test"))

    objects = TownQuerySet.as_manager()

    class Meta:
        ordering = ["kind", "name"]
        unique_together = [("municipality", "slug")]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("programs:detail", args=[self.pk, self.slug])

    def evaluate(self, profile):
        """Return (eligible, reasons) for a profile dict built by EligibilityForm."""
        reasons = []
        age = profile.get("age")
        if self.min_age is not None:
            if age is None or age < self.min_age:
                return False, []
            reasons.append(_("Age %(n)s or older") % {"n": self.min_age})
        if self.max_age is not None:
            if age is None or age > self.max_age:
                return False, []
            reasons.append(_("Age %(n)s or younger") % {"n": self.max_age})
        if self.max_monthly_income is not None:
            income = profile.get("income")
            if income is None or income > self.max_monthly_income:
                return False, []
            reasons.append(_("Household income within the limit"))
        if self.requires_farmer_or_fisherfolk:
            if not (profile.get("farmer") or profile.get("fisherfolk")):
                return False, []
            reasons.append(_("Farmer or fisherfolk"))
        for key, label in PROFILE_FLAGS:
            if getattr(self, f"requires_{key}"):
                if not profile.get(key):
                    return False, []
                reasons.append(label)
        return True, reasons


class ProgramSchedule(TimeStampedModel):
    """Application periods, payouts, orientations and similar announcements."""

    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="schedules")
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=160)
    opens_on = models.DateField()
    closes_on = models.DateField(null=True, blank=True)
    venue = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)

    objects = TownQuerySet.as_manager()

    class Meta:
        ordering = ["opens_on"]

    def __str__(self):
        return self.title

    @property
    def is_open(self):
        today = timezone.localdate()
        return self.opens_on <= today and (self.closes_on is None or self.closes_on >= today)
