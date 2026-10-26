from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import Municipality, TimeStampedModel, TownQuerySet


class FAQEntry(TimeStampedModel):
    """Answers for the help assistant, stored in English, Filipino and Romblomanon."""

    class Topic(models.TextChoices):
        SERVICES = "services", _("Services")
        PROGRAMS = "programs", _("Programs")
        TRANSPORT = "transport", _("Ferry & transport")
        TOURISM = "tourism", _("Tourism")
        EMERGENCY = "emergency", _("Emergency")
        GENERAL = "general", _("General")

    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, null=True, blank=True)
    topic = models.CharField(max_length=10, choices=Topic.choices)
    question = models.CharField(max_length=255)
    answer = models.TextField()
    keywords = models.CharField(max_length=255, blank=True, help_text=_("Extra search words, comma-separated"))
    link_url = models.CharField(max_length=200, blank=True, help_text=_("Site path for 'learn more', e.g. /ferry/"))
    is_published = models.BooleanField(default=True)

    objects = TownQuerySet.as_manager()

    class Meta:
        ordering = ["topic", "question"]
        verbose_name = "FAQ entry"
        verbose_name_plural = "FAQ entries"

    def __str__(self):
        return self.question


class AssistantQuery(models.Model):
    """Anonymous log (no personal data) used to find gaps in the FAQ."""

    question = models.CharField(max_length=500)
    language = models.CharField(max_length=5)
    layer = models.CharField(max_length=8, help_text=_("faq, site, llm or none"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "assistant queries"

    def __str__(self):
        return self.question[:60]
