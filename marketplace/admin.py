from django.contrib import admin

from core.admin_mixins import MunicipalityScopedAdmin

from .models import JobPosting, Listing


@admin.register(Listing)
class ListingAdmin(MunicipalityScopedAdmin):
    list_display = ("title", "kind", "municipality", "seller_name", "price", "is_approved")
    list_filter = ("kind", "municipality", "is_approved")
    list_editable = ("is_approved",)
    search_fields = ("title", "seller_name")


@admin.register(JobPosting)
class JobPostingAdmin(MunicipalityScopedAdmin):
    list_display = ("title", "employer", "kind", "municipality", "deadline", "is_approved")
    list_filter = ("kind", "municipality", "is_approved")
    list_editable = ("is_approved",)
