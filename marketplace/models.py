from django.db import models
from django.utils.translation import gettext_lazy as _

from core.images import compress_new_images
from core.models import Municipality, TimeStampedModel, TownQuerySet


class Listing(TimeStampedModel):
    """A local product. Listings stay hidden until staff approve them."""

    class Kind(models.TextChoices):
        HONEY = "honey", _("Wild Sibuyan honey")
        BALITSAW = "balitsaw", _("Balitsaw")
        WOVEN = "woven", _("Handwoven goods")
        FARM = "farm", _("Farm products")
        FISH = "fish", _("Fish & seafood")
        OTHER = "other", _("Other")

    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE)
    kind = models.CharField(max_length=10, choices=Kind.choices)
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)
    unit = models.CharField(max_length=40, blank=True, help_text=_("e.g. per bottle, per kilo"))
    seller_name = models.CharField(max_length=120)
    contact_phone = models.CharField(max_length=40)
    image = models.ImageField(upload_to="market/", blank=True)
    is_approved = models.BooleanField(default=False)
    expires_on = models.DateField(null=True, blank=True)

    objects = TownQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        compress_new_images(self, "image")
        super().save(*args, **kwargs)


class JobPosting(TimeStampedModel):
    class Kind(models.TextChoices):
        LGU = "lgu", _("LGU job / plantilla")
        PRIVATE = "private", _("Local business")
        LIVELIHOOD = "livelihood", _("Livelihood / training")

    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, null=True, blank=True)
    kind = models.CharField(max_length=10, choices=Kind.choices)
    employer = models.CharField(max_length=160)
    title = models.CharField(max_length=160)
    description = models.TextField()
    pay = models.CharField(max_length=120, blank=True)
    how_to_apply = models.TextField()
    deadline = models.DateField(null=True, blank=True)
    is_approved = models.BooleanField(default=False)

    objects = TownQuerySet.as_manager()

    class Meta:
        ordering = ["deadline"]

    def __str__(self):
        return f"{self.title} - {self.employer}"
