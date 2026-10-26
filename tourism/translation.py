from modeltranslation.translator import TranslationOptions, register

from .models import Attraction, Business, ClimbAdvisory, TravelRule


@register(Attraction)
class AttractionTR(TranslationOptions):
    fields = ("summary", "description", "tips", "best_time", "getting_there", "guide_requirement", "fee_notes",
              "closure_note")


@register(ClimbAdvisory)
class ClimbAdvisoryTR(TranslationOptions):
    fields = ("season_note", "permit_requirements")


@register(Business)
class BusinessTR(TranslationOptions):
    fields = ("description",)


@register(TravelRule)
class TravelRuleTR(TranslationOptions):
    fields = ("title", "body")
