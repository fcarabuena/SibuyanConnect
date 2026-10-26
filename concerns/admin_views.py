"""First-party analytics for the CMS. Uses only the site's own database."""
from datetime import timedelta

from django.contrib import admin
from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, Q
from django.shortcuts import render
from django.utils import timezone

from programs.models import Program
from services.models import Service

from .models import Concern


def analytics_view(request):
    since = timezone.now() - timedelta(days=int(request.GET.get("days", 90)))
    concerns = Concern.objects.filter(created_at__gte=since)
    profile = getattr(request.user, "staff_profile", None)
    if not request.user.is_superuser and profile and profile.municipality_id:
        concerns = concerns.filter(municipality_id=profile.municipality_id)

    by_office = (
        concerns.values("office__name", "municipality__name")
        .annotate(
            total=Count("id"),
            open=Count("id", filter=~Q(status=Concern.Status.RESOLVED)),
            resolved=Count("id", filter=Q(status=Concern.Status.RESOLVED)),
            avg_resolution=Avg(
                ExpressionWrapper(F("resolved_at") - F("created_at"), output_field=DurationField()),
                filter=Q(resolved_at__isnull=False),
            ),
        )
        .order_by("-total")
    )
    rows = []
    for row in by_office:
        avg = row["avg_resolution"]
        row["avg_hours"] = round(avg.total_seconds() / 3600, 1) if avg else None
        rows.append(row)

    context = {
        **admin.site.each_context(request),
        "title": "Analytics",
        "days": request.GET.get("days", 90),
        "by_office": rows,
        "by_status": concerns.values("status").annotate(n=Count("id")).order_by("status"),
        "by_category": concerns.values("category__name").annotate(n=Count("id")).order_by("-n")[:10],
        "total": concerns.count(),
        "top_services": Service.objects.order_by("-view_count").select_related("municipality")[:10],
        "top_programs": Program.objects.order_by("-view_count")[:10],
    }
    return render(request, "admin/analytics.html", context)
