from django.contrib import admin
from modeltranslation.admin import TranslationAdmin, TranslationTabularInline

from core.admin_mixins import MunicipalityScopedAdmin

from .models import Program, ProgramSchedule


class ScheduleInline(TranslationTabularInline):
    model = ProgramSchedule
    extra = 0


@admin.register(Program)
class ProgramAdmin(MunicipalityScopedAdmin, TranslationAdmin):
    list_display = ("name", "agency", "level", "kind", "municipality", "view_count", "is_published")
    list_filter = ("level", "kind", "municipality", "is_published")
    search_fields = ("name", "agency", "summary")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ScheduleInline]
    fieldsets = (
        (None, {"fields": ("municipality", "level", "kind", "agency", "name", "slug", "summary",
                           "benefits", "how_to_apply", "contact_office", "official_url", "is_published")}),
        ("Eligibility rules (used by the eligibility checker)", {"fields": (
            ("min_age", "max_age", "max_monthly_income"),
            ("requires_student", "requires_farmer", "requires_fisherfolk", "requires_farmer_or_fisherfolk"),
            ("requires_pwd", "requires_solo_parent", "requires_indigenous"),
            ("requires_informal_worker", "requires_in_crisis", "requires_listahanan_poor"),
            "eligibility_notes",
        )}),
    )


@admin.register(ProgramSchedule)
class ProgramScheduleAdmin(MunicipalityScopedAdmin, TranslationAdmin):
    list_display = ("title", "program", "municipality", "opens_on", "closes_on")
    list_filter = ("municipality",)
