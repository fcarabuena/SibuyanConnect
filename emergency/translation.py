from modeltranslation.translator import TranslationOptions, register

from .models import Hotline, PreparednessGuide


@register(Hotline)
class HotlineTR(TranslationOptions):
    fields = ("name",)


@register(PreparednessGuide)
class PreparednessGuideTR(TranslationOptions):
    fields = ("title", "body")
