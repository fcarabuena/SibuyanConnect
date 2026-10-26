from django import forms
from django.utils.translation import gettext_lazy as _

from core.images import compress_image

from .models import Concern


class ConcernForm(forms.ModelForm):
    consent = forms.BooleanField(
        required=True,
        label=_("I agree that the LGU may use the information above to act on my concern, "
                "as described in the Privacy Notice."),
    )

    class Meta:
        model = Concern
        fields = [
            "municipality", "barangay", "category", "subject", "description",
            "location_detail", "photo", "name", "email", "phone",
        ]
        labels = {
            "municipality": _("Town"),
            "subject": _("Short title"),
            "description": _("What happened? Please give details"),
            "photo": _("Photo (optional)"),
            "name": _("Your name"),
            "email": _("Email (for updates)"),
            "phone": _("Mobile number"),
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "phone": forms.TextInput(attrs={"inputmode": "tel", "autocomplete": "tel", "placeholder": "09XX XXX XXXX"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "name": forms.TextInput(attrs={"autocomplete": "name"}),
            "photo": forms.ClearableFileInput(attrs={"accept": "image/*", "capture": "environment"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["barangay"].queryset = self.fields["barangay"].queryset.select_related("municipality")

    def clean_photo(self):
        photo = self.cleaned_data.get("photo")
        if photo and hasattr(photo, "content_type"):
            return compress_image(photo)
        return photo

    def clean(self):
        data = super().clean()
        town, barangay = data.get("municipality"), data.get("barangay")
        if town and barangay and barangay.municipality_id != town.pk:
            self.add_error("barangay", _("This barangay is not in the selected town."))
        if not data.get("email") and not data.get("phone"):
            raise forms.ValidationError(_("Please give an email or a mobile number so the LGU can reach you."))
        return data


class TrackForm(forms.Form):
    ticket_number = forms.CharField(label=_("Ticket number"), max_length=24,
                                    widget=forms.TextInput(attrs={"placeholder": "SC-MAG-2026-00001"}))
    contact = forms.CharField(label=_("Email or mobile number you used"), max_length=120)


class MessageForm(forms.Form):
    body = forms.CharField(label=_("Message"), widget=forms.Textarea(attrs={"rows": 3}), max_length=2000)
