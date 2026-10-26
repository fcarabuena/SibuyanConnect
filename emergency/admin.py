from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from core.admin_mixins import MunicipalityScopedAdmin, staff_municipality

from .models import EvacuationCenter, Hotline, PreparednessGuide


@admin.register(Hotline)
class HotlineAdmin(MunicipalityScopedAdmin, TranslationAdmin):
    list_display = ("name", "agency", "municipality", "number", "is_24h", "is_verified", "order")
    list_filter = ("agency", "municipality", "is_verified")
    list_editable = ("order", "is_verified")


@admin.register(EvacuationCenter)
class EvacuationCenterAdmin(admin.ModelAdmin):
    list_display = ("name", "barangay", "capacity")
    list_filter = ("barangay__municipality",)
    search_fields = ("name", "barangay__name")

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("barangay__municipality")
        town = staff_municipality(request.user)
        return qs if town is None else qs.filter(barangay__municipality=town)


@admin.register(PreparednessGuide)
class PreparednessGuideAdmin(TranslationAdmin):
    list_display = ("title", "hazard", "order")
