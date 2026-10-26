from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from core.admin_mixins import MunicipalityScopedAdmin, staff_municipality

from .models import JeepneySchedule, Route, TricycleFare, Trip


@admin.register(Route)
class RouteAdmin(MunicipalityScopedAdmin, TranslationAdmin):
    list_display = ("__str__", "port", "schedule_text", "is_active")
    list_filter = ("municipality", "is_active")


@admin.register(Trip)
class TripAdmin(TranslationAdmin):
    """Port / LGU staff update sailing status here, ideally right from the list view."""

    list_display = ("route", "departure_date", "departure_time", "status", "status_note", "updated_at")
    list_editable = ("status", "status_note")
    list_filter = ("status", "departure_date", "route__municipality")
    date_hierarchy = "departure_date"
    exclude = ("updated_by",)

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("route")
        town = staff_municipality(request.user)
        return qs if town is None else qs.filter(route__municipality=town)

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(JeepneySchedule)
class JeepneyScheduleAdmin(admin.ModelAdmin):
    list_display = ("origin", "destination", "terminal", "departure_time", "days", "fare")
    list_filter = ("origin", "destination")


@admin.register(TricycleFare)
class TricycleFareAdmin(MunicipalityScopedAdmin):
    list_display = ("municipality", "from_point", "to_point", "regular_fare", "discounted_fare")
    list_filter = ("municipality",)
