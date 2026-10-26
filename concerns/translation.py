from modeltranslation.translator import TranslationOptions, register

from .models import ConcernCategory


@register(ConcernCategory)
class ConcernCategoryTR(TranslationOptions):
    fields = ("name", "description")
