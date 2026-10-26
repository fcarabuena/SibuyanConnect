from django.contrib import admin
from modeltranslation.admin import TranslationAdmin, TranslationStackedInline

from core.admin_mixins import MunicipalityScopedAdmin

from .models import Attraction, Business, ClimbAdvisory, TravelRule


class AdvisoryInline(TranslationStackedInline):
    model = ClimbAdvisory
    extra = 0


@admin.register(Attraction)
class AttractionAdmin(MunicipalityScopedAdmin, TranslationAdmin):
    list_display = ("name", "kind", "municipality", "environmental_fee", "is_protected_area", "is_open")
    list_filter = ("kind", "municipality", "is_protected_area", "is_open")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [AdvisoryInline]


@admin.register(Business)
class BusinessAdmin(MunicipalityScopedAdmin, TranslationAdmin):
    list_display = ("name", "kind", "municipality", "is_accredited", "accredited_by")
    list_filter = ("kind", "municipality", "is_accredited")
    search_fields = ("name",)


@admin.register(TravelRule)
class TravelRuleAdmin(TranslationAdmin):
    list_display = ("title", "scope", "order")
    list_filter = ("scope",)
