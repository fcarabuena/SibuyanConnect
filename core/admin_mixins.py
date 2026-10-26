from django.contrib import admin


def staff_municipality(user):
    """The municipality a staff user is limited to, or None for island-wide staff."""
    if user.is_superuser:
        return None
    profile = getattr(user, "staff_profile", None)
    return profile.municipality if profile else None


class MunicipalityScopedAdmin(admin.ModelAdmin):
    """Per-municipality admins and editors only see and edit their own town's records.

    Island-wide records (municipality empty) are visible to everyone but only
    editable by island-wide staff.
    """

    municipality_field = "municipality"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        town = staff_municipality(request.user)
        if town is None:
            return qs
        return qs.filter(**{self.municipality_field: town})

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        town = staff_municipality(request.user)
        if town is not None and db_field.name == "municipality":
            kwargs["queryset"] = db_field.related_model.objects.filter(pk=town.pk)
            kwargs["initial"] = town.pk
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        town = staff_municipality(request.user)
        if town is not None and self.municipality_field == "municipality":
            obj.municipality = town
        super().save_model(request, obj, form, change)
