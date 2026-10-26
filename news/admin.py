from django.contrib import admin
from modeltranslation.admin import TranslationAdmin, TranslationTabularInline

from core.admin_mixins import MunicipalityScopedAdmin

from .models import Event, EventPhoto, Post


@admin.register(Post)
class PostAdmin(MunicipalityScopedAdmin, TranslationAdmin):
    list_display = ("title", "category", "municipality", "is_pinned", "is_published", "published_at")
    list_filter = ("category", "municipality", "is_pinned", "is_published")
    list_editable = ("is_pinned", "is_published")
    search_fields = ("title", "summary")
    prepopulated_fields = {"slug": ("title",)}
    exclude = ("author",)

    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)


class PhotoInline(TranslationTabularInline):
    model = EventPhoto
    extra = 1


@admin.register(Event)
class EventAdmin(MunicipalityScopedAdmin, TranslationAdmin):
    list_display = ("title", "kind", "municipality", "starts_on", "ends_on", "is_published")
    list_filter = ("kind", "municipality")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [PhotoInline]
