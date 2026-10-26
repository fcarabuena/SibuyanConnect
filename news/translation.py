from modeltranslation.translator import TranslationOptions, register

from .models import Event, EventPhoto, Post


@register(Post)
class PostTR(TranslationOptions):
    fields = ("title", "summary", "body")


@register(Event)
class EventTR(TranslationOptions):
    fields = ("title", "description", "venue")


@register(EventPhoto)
class EventPhotoTR(TranslationOptions):
    fields = ("caption",)
