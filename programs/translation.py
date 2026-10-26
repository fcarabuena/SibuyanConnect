from modeltranslation.translator import TranslationOptions, register

from .models import Program, ProgramSchedule


@register(Program)
class ProgramTR(TranslationOptions):
    fields = ("name", "summary", "benefits", "how_to_apply", "eligibility_notes")


@register(ProgramSchedule)
class ProgramScheduleTR(TranslationOptions):
    fields = ("title", "notes")
