from modeltranslation.translator import TranslationOptions, register

from .models import Alert, Municipality


@register(Municipality)
class MunicipalityTR(TranslationOptions):
    fields = ("tagline", "description")


@register(Alert)
class AlertTR(TranslationOptions):
    fields = ("title", "body")
