from modeltranslation.translator import TranslationOptions, register

from .models import Route, Trip


@register(Route)
class RouteTR(TranslationOptions):
    fields = ("schedule_text", "notes")


@register(Trip)
class TripTR(TranslationOptions):
    fields = ("status_note",)
