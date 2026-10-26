from modeltranslation.translator import TranslationOptions, register

from .models import EnvironmentUpdate, PublicDocument


@register(PublicDocument)
class PublicDocumentTR(TranslationOptions):
    fields = ("title", "summary")


@register(EnvironmentUpdate)
class EnvironmentUpdateTR(TranslationOptions):
    fields = ("title", "body")
