from modeltranslation.translator import TranslationOptions, register

from .models import Service, ServiceCategory, ServiceForm, ServiceRequirement, ServiceStep


@register(ServiceCategory)
class ServiceCategoryTR(TranslationOptions):
    fields = ("name",)


@register(Service)
class ServiceTR(TranslationOptions):
    fields = ("name", "summary", "who_may_apply", "fees", "processing_time")


@register(ServiceStep)
class ServiceStepTR(TranslationOptions):
    fields = ("description",)


@register(ServiceRequirement)
class ServiceRequirementTR(TranslationOptions):
    fields = ("text", "where_to_get", "condition")


@register(ServiceForm)
class ServiceFormTR(TranslationOptions):
    fields = ("title",)
