from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from .models import Concern, ConcernCategory, ConcernMessage, StatusChange
from .notifications import notify_reply, notify_status


@admin.register(ConcernCategory)
class ConcernCategoryAdmin(TranslationAdmin):
    list_display = ("name", "office_kind", "order")
    prepopulated_fields = {"slug": ("name",)}


class MessageInline(admin.StackedInline):
    model = ConcernMessage
    extra = 1
    fields = ("sender", "author", "body", "is_internal", "created_at")
    readonly_fields = ("sender", "author", "created_at")
    can_delete = False

    def has_change_permission(self, request, obj=None):
        return False  # messages are an audit trail: add, never edit


class StatusChangeInline(admin.TabularInline):
    model = StatusChange
    extra = 0
    readonly_fields = ("from_status", "to_status", "changed_by", "note", "created_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Concern)
class ConcernAdmin(admin.ModelAdmin):
    list_display = ("ticket_number", "subject", "category", "municipality", "barangay", "office",
                    "status", "priority", "created_at")
    list_filter = ("status", "priority", "municipality", "office", "category")
    search_fields = ("ticket_number", "subject", "description", "name")
    date_hierarchy = "created_at"
    readonly_fields = ("ticket_number", "created_at", "updated_at", "resolved_at", "consent_given_at",
                       "privacy_notice_version", "source", "citizen")
    autocomplete_fields = ("assigned_to",)
    inlines = [MessageInline, StatusChangeInline]
    actions = ["mark_in_progress", "mark_resolved"]
    fieldsets = (
        ("Ticket", {"fields": ("ticket_number", "status", "priority", "office", "assigned_to",
                               "created_at", "resolved_at")}),
        ("Concern", {"fields": ("category", "subject", "description", "municipality", "barangay",
                                "location_detail", "photo")}),
        ("Citizen contact (personal data - RA 10173)", {"fields": (
            "name", "email", "phone", "citizen", "consent_given_at", "privacy_notice_version", "source")}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("office", "municipality", "barangay", "category")
        if request.user.is_superuser:
            return qs
        profile = getattr(request.user, "staff_profile", None)
        if profile is None:
            return qs.none()
        if profile.office_id:
            return qs.filter(office_id=profile.office_id)
        if profile.municipality_id:
            return qs.filter(municipality_id=profile.municipality_id)
        return qs

    def _record_status(self, request, obj, old_status, note=""):
        if old_status != obj.status:
            StatusChange.objects.create(
                concern=obj, from_status=old_status or "", to_status=obj.status,
                changed_by=request.user, note=note,
            )
            obj.messages.create(sender=ConcernMessage.Sender.SYSTEM,
                                body=f"Status changed to {obj.get_status_display()}.")
            notify_status(obj, request)

    def save_model(self, request, obj, form, change):
        old_status = Concern.objects.filter(pk=obj.pk).values_list("status", flat=True).first() if change else None
        if obj.assigned_to_id and obj.status == Concern.Status.RECEIVED:
            obj.status = Concern.Status.ASSIGNED
        super().save_model(request, obj, form, change)
        if change:
            self._record_status(request, obj, old_status)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for inst in instances:
            if isinstance(inst, ConcernMessage) and inst.pk is None:
                inst.author = request.user
                inst.sender = ConcernMessage.Sender.STAFF
                inst.save()
                if not inst.is_internal:
                    notify_reply(inst.concern, inst, request)
            else:
                inst.save()
        formset.save_m2m()

    def _bulk_status(self, request, queryset, status):
        for concern in queryset:
            old = concern.status
            concern.status = status
            concern.save()
            self._record_status(request, concern, old, note="bulk action")

    @admin.action(description="Mark selected as In progress")
    def mark_in_progress(self, request, queryset):
        self._bulk_status(request, queryset, Concern.Status.IN_PROGRESS)

    @admin.action(description="Mark selected as Resolved")
    def mark_resolved(self, request, queryset):
        self._bulk_status(request, queryset, Concern.Status.RESOLVED)
