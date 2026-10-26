"""Move dated SAMPLE records (sailings, schedules, alerts, news, events) so they start today.

The fixture was generated on a fixed day; run this after `loaddata sample_data`
so the ferry board, alerts and schedules look current in a demo.
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import F, Min
from django.utils import timezone

from concerns.models import Concern
from core.models import Alert
from news.models import Event, Post
from programs.models import ProgramSchedule
from transport.models import Trip


class Command(BaseCommand):
    help = "Shift sample dates so the earliest sample sailing is today."

    def handle(self, *args, **opts):
        anchor = Trip.objects.aggregate(d=Min("departure_date"))["d"]
        if anchor is None:
            self.stdout.write("No sailings found; nothing to shift.")
            return
        delta = timezone.localdate() - anchor
        if not delta:
            self.stdout.write("Sample dates are already current.")
            return
        Trip.objects.update(departure_date=F("departure_date") + delta)
        ProgramSchedule.objects.update(opens_on=F("opens_on") + delta, closes_on=F("closes_on") + delta)
        Event.objects.update(starts_on=F("starts_on") + delta, ends_on=F("ends_on") + delta)
        Alert.objects.update(starts_at=F("starts_at") + delta, ends_at=F("ends_at") + delta)
        Post.objects.update(published_at=F("published_at") + delta)
        Concern.objects.update(created_at=F("created_at") + delta, resolved_at=F("resolved_at") + delta)
        self.stdout.write(self.style.SUCCESS(f"Shifted sample dates by {delta.days} days."))
