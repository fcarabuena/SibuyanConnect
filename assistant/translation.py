from modeltranslation.translator import TranslationOptions, register

from .models import FAQEntry


@register(FAQEntry)
class FAQEntryTR(TranslationOptions):
    fields = ("question", "answer", "keywords")
