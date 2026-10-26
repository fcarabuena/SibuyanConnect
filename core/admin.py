from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from .admin_mixins import MunicipalityScopedAdmin
from .models import Alert, AlertSubscription, Barangay, Municipality, Office, StaffProfile
from .notify import send_email


class BarangayInline(admin.TabularInline):
    model = Barangay
    extra = 0


@admin.register(Municipality)
class MunicipalityAdmin(TranslationAdmin):
    list_display = ("name", "code", "order")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [BarangayInline]


@admin.register(Barangay)
class BarangayAdmin(admin.ModelAdmin):
    list_display = ("name", "municipality")
    list_filter = ("municipality",)
    search_fields = ("name",)


@admin.register(Office)
class OfficeAdmin(MunicipalityScopedAdmin):
    list_display = ("name", "kind", "municipality", "phone", "email")
    list_filter = ("municipality", "kind")
    search_fields = ("name", "head")


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "municipality", "office", "position")
    list_filter = ("municipality",)
    autocomplete_fields = ("user",)


@admin.register(Alert)
class AlertAdmin(MunicipalityScopedAdmin, TranslationAdmin):
    list_display = ("title", "kind", "level", "municipality", "starts_at", "ends_at", "is_active")
    list_filter = ("kind", "level", "is_active", "municipality")
    list_editable = ("is_active",)
    search_fields = ("title",)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.notify_subscribers:
            subs = AlertSubscription.objects.filter(is_active=True)
            if obj.municipality_id:
                subs = subs.filter(municipality__in=[obj.municipality_id, None])
            body = f"{obj.body}\n\n{obj.source_url}".strip()
            sent = send_email(list(subs.values_list("email", flat=True)), f"[SibuyanConnect] {obj.title}", body)
            obj.notify_subscribers = False
            obj.save(update_fields=["notify_subscribers"])
            self.message_user(request, f"Alert emailed ({sent} message batch sent).")


@admin.register(AlertSubscription)
class AlertSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("email", "municipality", "is_active", "consent_given_at")
    list_filter = ("municipality", "is_active")
