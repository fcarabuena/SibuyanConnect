from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from core.admin_mixins import MunicipalityScopedAdmin

from .models import AssistantQuery, FAQEntry


@admin.register(FAQEntry)
class FAQEntryAdmin(MunicipalityScopedAdmin, TranslationAdmin):
    list_display = ("question", "topic", "municipality", "is_published")
    list_filter = ("topic", "municipality", "is_published")
    search_fields = ("question", "answer", "keywords")


@admin.register(AssistantQuery)
class AssistantQueryAdmin(admin.ModelAdmin):
    """Unanswered questions (layer = none) show what the FAQ is missing."""

    list_display = ("question", "language", "layer", "created_at")
    list_filter = ("layer", "language")
    search_fields = ("question",)

    def has_add_permission(self, request):
        return False
