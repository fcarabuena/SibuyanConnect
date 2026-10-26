"""Create demo staff accounts, one per role, for trying out the CMS locally.

    python manage.py create_demo_staff

Refuses to run when DEBUG is off unless --force is given, because the
password is shared and printed. Never use these accounts in production.
"""
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand, CommandError

from core.models import Municipality, Office, StaffProfile

DEMO_PASSWORD = "sibuyan-demo-2026"


class Command(BaseCommand):
    help = "Create demo staff accounts (DEBUG only)."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true")

    def handle(self, *args, **opts):
        if not settings.DEBUG and not opts["force"]:
            raise CommandError("Refusing to create demo accounts with DEBUG off.")
        mag = Municipality.objects.get(code="MAG")
        accounts = [
            ("superadmin", "Super Admin", None, None, True),
            ("mag_admin", "Municipal Admin", mag, None, False),
            ("mag_engineering", "Department Staff", mag, Office.objects.get(municipality=mag, kind=Office.Kind.ENGINEERING), False),
            ("mag_mswdo", "Department Staff", mag, Office.objects.get(municipality=mag, kind=Office.Kind.MSWDO), False),
            ("editor", "Content Editor", None, None, False),
        ]
        for username, role, town, office, superuser in accounts:
            user, _ = User.objects.get_or_create(username=username)
            user.is_staff = True
            user.is_superuser = superuser
            user.email = f"{username}@example.com"
            user.set_password(DEMO_PASSWORD)
            user.save()
            user.groups.set([Group.objects.get(name=role)])
            StaffProfile.objects.update_or_create(
                user=user, defaults={"municipality": town, "office": office, "position": f"Demo {role}"}
            )
            scope = office or town or "island-wide"
            self.stdout.write(f"  {username:16} {role:17} {scope}")
        self.stdout.write(self.style.WARNING(f"Password for all demo accounts: {DEMO_PASSWORD}"))
