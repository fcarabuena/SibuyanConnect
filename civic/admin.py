from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from core.admin_mixins import MunicipalityScopedAdmin

from .models import EnvironmentUpdate, Official, PublicDocument


@admin.register(PublicDocument)
class PublicDocumentAdmin(MunicipalityScopedAdmin, TranslationAdmin):
    list_display = ("__str__", "kind", "municipality", "date_issued")
    list_filter = ("kind", "municipality")
    search_fields = ("title", "number")
    date_hierarchy = "date_issued"


@admin.register(Official)
class OfficialAdmin(MunicipalityScopedAdmin):
    list_display = ("name", "position", "municipality", "term", "order")
    list_filter = ("municipality",)
    list_editable = ("order",)


@admin.register(EnvironmentUpdate)
class EnvironmentUpdateAdmin(MunicipalityScopedAdmin, TranslationAdmin):
    list_display = ("title", "kind", "municipality", "source", "published_at")
    list_filter = ("kind", "municipality")
