from django.contrib import admin
from modeltranslation.admin import TranslationAdmin, TranslationTabularInline

from core.admin_mixins import MunicipalityScopedAdmin

from .models import Service, ServiceCategory, ServiceForm, ServiceRequirement, ServiceStep


class StepInline(TranslationTabularInline):
    model = ServiceStep
    extra = 0


class RequirementInline(TranslationTabularInline):
    model = ServiceRequirement
    extra = 0


class FormInline(TranslationTabularInline):
    model = ServiceForm
    extra = 0


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(TranslationAdmin):
    list_display = ("name", "icon", "order")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Service)
class ServiceAdmin(MunicipalityScopedAdmin, TranslationAdmin):
    list_display = ("name", "municipality", "category", "office", "fee_amount", "view_count", "is_published")
    list_filter = ("municipality", "category", "is_published")
    search_fields = ("name", "summary")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("view_count",)
    inlines = [RequirementInline, StepInline, FormInline]
