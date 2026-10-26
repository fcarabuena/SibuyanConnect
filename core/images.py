"""Shrink uploaded photos with Pillow so pages stay light on weak mobile data."""
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageOps


def compress_image(uploaded, max_dim=None, quality=None):
    """Return a ContentFile with the image resized to max_dim and saved as JPEG.

    EXIF data (which can include GPS location) is dropped for privacy.
    """
    max_dim = max_dim or settings.IMAGE_MAX_DIMENSION
    quality = quality or settings.IMAGE_JPEG_QUALITY
    uploaded.seek(0)
    img = Image.open(uploaded)
    img = ImageOps.exif_transpose(img)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img.thumbnail((max_dim, max_dim))
    out = BytesIO()
    img.save(out, format="JPEG", quality=quality, optimize=True, progressive=True)
    name = Path(getattr(uploaded, "name", "photo")).stem + ".jpg"
    return ContentFile(out.getvalue(), name=name)


def compress_new_images(instance, *field_names):
    """Call from a model's save(): compress any image field holding a fresh upload."""
    for name in field_names:
        field_file = getattr(instance, name)
        if field_file and not getattr(field_file, "_committed", True):
            compressed = compress_image(field_file.file)
            field_file.save(compressed.name, compressed, save=False)
