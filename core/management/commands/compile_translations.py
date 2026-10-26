"""Compile locale/*/LC_MESSAGES/django.po to .mo using polib.

Django's own `compilemessages` needs GNU gettext, which is awkward to install
on Windows and some free hosts. This pure-Python command does the same job.
"""
from pathlib import Path

import polib
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Compile .po translation files to .mo without GNU gettext."

    def handle(self, *args, **opts):
        for locale_dir in settings.LOCALE_PATHS:
            for po_path in Path(locale_dir).glob("*/LC_MESSAGES/*.po"):
                po = polib.pofile(str(po_path))
                po.save_as_mofile(str(po_path.with_suffix(".mo")))
                self.stdout.write(f"{po_path} ({po.percent_translated()}% translated)")
