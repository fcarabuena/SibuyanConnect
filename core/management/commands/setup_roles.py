"""Create the four staff roles as Django groups with sensible permissions.

    python manage.py setup_roles

Safe to re-run: permissions are reset to the definitions below each time.
"""
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

CONTENT_MODELS = [
    "news.post", "news.event", "news.eventphoto",
    "services.service", "services.servicerequirement", "services.servicestep", "services.serviceform",
    "services.servicecategory",
    "programs.program", "programs.programschedule",
    "transport.route", "transport.trip", "transport.jeepneyschedule", "transport.tricyclefare",
    "tourism.attraction", "tourism.business", "tourism.climbadvisory", "tourism.travelrule",
    "emergency.hotline", "emergency.evacuationcenter", "emergency.preparednessguide",
    "marketplace.listing", "marketplace.jobposting",
    "civic.publicdocument", "civic.official", "civic.environmentupdate",
    "assistant.faqentry",
    "core.alert",
]
TICKET_MODELS = ["concerns.concern", "concerns.concernmessage", "concerns.statuschange"]
ALL = ("add", "change", "delete", "view")

ROLES = {
    # Island-wide administrators. Also give them is_superuser if they manage users.
    "Super Admin": {"*": ALL},
    # Full control of their own town's content and tickets (scoped by StaffProfile).
    "Municipal Admin": {
        **{m: ALL for m in CONTENT_MODELS},
        **{m: ALL for m in TICKET_MODELS},
        "core.office": ("add", "change", "view"),
        "core.staffprofile": ("view",),
        "concerns.concerncategory": ("view",),
        "core.barangay": ("view",),
    },
    # Handle tickets routed to their office.
    "Department Staff": {
        "concerns.concern": ("change", "view"),
        "concerns.concernmessage": ("add", "view"),
        "concerns.statuschange": ("view",),
        "services.service": ("change", "view"),
        "transport.trip": ("change", "view"),
    },
    # Publish news, events, schedules and directory content; no ticket access.
    "Content Editor": {m: ("add", "change", "view") for m in CONTENT_MODELS},
}


class Command(BaseCommand):
    help = "Create or update staff role groups and their permissions."

    def handle(self, *args, **opts):
        for role, spec in ROLES.items():
            group, _ = Group.objects.get_or_create(name=role)
            if "*" in spec:
                perms = Permission.objects.all()
            else:
                perms = []
                for model_label, actions in spec.items():
                    app_label, model = model_label.split(".")
                    for action in actions:
                        perm = Permission.objects.filter(
                            content_type__app_label=app_label, codename=f"{action}_{model}"
                        ).first()
                        if perm is None:
                            self.stderr.write(f"  missing permission {action}_{model_label}")
                        else:
                            perms.append(perm)
            group.permissions.set(perms)
            self.stdout.write(self.style.SUCCESS(f"{role}: {len(perms)} permissions"))
