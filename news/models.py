from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.images import compress_new_images
from core.models import Municipality, TimeStampedModel, TownQuerySet


class PostQuerySet(TownQuerySet):
    def published(self):
        return self.filter(is_published=True, published_at__lte=timezone.now())


class Post(TimeStampedModel):
    class Category(models.TextChoices):
        LGU = "lgu", _("LGU announcement")
        ADVISORY = "advisory", _("Advisory")
        EVENT = "event", _("Event")
        HEALTH = "health", _("Health")
        AGRICULTURE = "agriculture", _("Agriculture")
        EDUCATION = "education", _("Education")

    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, null=True, blank=True)
    category = models.CharField(max_length=12, choices=Category.choices)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    summary = models.CharField(max_length=300)
    body = models.TextField()
    image = models.ImageField(upload_to="news/%Y/", blank=True)
    is_pinned = models.BooleanField(default=False, help_text=_("Pin urgent advisories to the top"))
    is_published = models.BooleanField(default=True)
    published_at = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    objects = PostQuerySet.as_manager()

    class Meta:
        ordering = ["-is_pinned", "-published_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        compress_new_images(self, "image")
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("news:detail", args=[self.pk, self.slug])


class Event(TimeStampedModel):
    class Kind(models.TextChoices):
        FIESTA = "fiesta", _("Town / barangay fiesta")
        FESTIVAL = "festival", _("Festival")
        LGU = "lgu", _("LGU event")
        COMMUNITY = "community", _("Community activity")

    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, null=True, blank=True)
    kind = models.CharField(max_length=10, choices=Kind.choices)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    description = models.TextField(blank=True)
    starts_on = models.DateField()
    ends_on = models.DateField(null=True, blank=True)
    venue = models.CharField(max_length=200, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    cover = models.ImageField(upload_to="events/", blank=True)
    is_published = models.BooleanField(default=True)

    objects = TownQuerySet.as_manager()

    class Meta:
        ordering = ["starts_on"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        compress_new_images(self, "cover")
        super().save(*args, **kwargs)


class EventPhoto(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="events/gallery/")
    caption = models.CharField(max_length=200, blank=True)
    credit = models.CharField(max_length=120, blank=True)

    def save(self, *args, **kwargs):
        compress_new_images(self, "image")
        super().save(*args, **kwargs)
