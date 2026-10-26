from django import forms
from django.utils.translation import gettext_lazy as _

from core.models import Municipality

from .models import PROFILE_FLAGS

INCOME_CHOICES = [
    ("", _("Prefer not to say")),
    ("5000", _("Below PHP 5,000")),
    ("10000", _("PHP 5,000 - 10,000")),
    ("15000", _("PHP 10,001 - 15,000")),
    ("25000", _("PHP 15,001 - 25,000")),
    ("40000", _("PHP 25,001 - 40,000")),
    ("999999", _("Above PHP 40,000")),
]


class EligibilityForm(forms.Form):
    """Nothing entered here is stored; it is only used to filter the program list."""

    town = forms.ModelChoiceField(
        queryset=Municipality.objects.all(), required=False, empty_label=_("Any town"), label=_("Where do you live?")
    )
    age = forms.IntegerField(min_value=0, max_value=120, required=False, label=_("Your age"))
    income = forms.ChoiceField(choices=INCOME_CHOICES, required=False, label=_("Household monthly income"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key, label in PROFILE_FLAGS:
            self.fields[key] = forms.BooleanField(required=False, label=label)

    def basic_fields(self):
        return [self["town"], self["age"], self["income"]]

    def flag_fields(self):
        return [self[key] for key, _ in PROFILE_FLAGS]

    def profile(self):
        data = dict(self.cleaned_data)
        data["income"] = int(data["income"]) if data.get("income") else None
        return data
