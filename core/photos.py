"""Registry of the site's photos: files, alt text and credits.

Every photo is free-licence and was taken on Sibuyan (checked against the
Commons description, GPS data where present, and the place shown). Files are
built by tools/build_photos.py. To add your own photo later, add an entry here
and its WebP files to static/img/photos/.
"""
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _

ANDROKOY = ("Androkoy", "CC BY-SA 4.0")

PHOTOS = {
    "hero-guiting": {
        "widths": [1100, 1600], "ratio": (16, 9),
        "alt": _("The forested range of Mt. Guiting-Guiting under a clear blue sky"),
        "author": "Dosias", "licence": "CC BY-SA 4.0",
        "source": "https://commons.wikimedia.org/wiki/File:Mt._Guiting_-_Guiting.jpg",
    },
    "hero-guiting-m": {
        "widths": [720], "ratio": (9, 8),
        "alt": _("The forested range of Mt. Guiting-Guiting under a clear blue sky"),
        "author": "Dosias", "licence": "CC BY-SA 4.0",
        "source": "https://commons.wikimedia.org/wiki/File:Mt._Guiting_-_Guiting.jpg",
    },
    # Crossfade slides play behind the hero gradient, so 1100 px is enough on desktop.
    "hero-coast": {
        "widths": [1100], "ratio": (16, 9),
        "alt": _("Sibuyan Island seen from the sea, its mountains under the clouds"),
        "author": "Patrickroque01", "licence": "CC BY-SA 4.0",
        "source": "https://commons.wikimedia.org/wiki/File:Sibuyan_Island_(Romblon;_12-05-2023).jpg",
    },
    "hero-cantingas": {
        "widths": [1100], "ratio": (16, 9),
        "alt": _("Clear water running over boulders in the Cantingas River, with forested hills behind"),
        "author": "Carlojoseph14", "licence": "CC BY-SA 4.0",
        "source": "https://commons.wikimedia.org/wiki/File:Cantingas_River.jpg",
    },
    "g-guiting": {
        "widths": [400, 800], "ratio": (4, 3),
        "alt": _("The summit of Mt. Guiting-Guiting glowing gold at sunrise"),
        "author": ANDROKOY[0], "licence": ANDROKOY[1],
        "source": "https://commons.wikimedia.org/wiki/File:Guiting-guiting_3.jpg",
    },
    "g-cantingas": {
        "widths": [400, 800], "ratio": (4, 3),
        "alt": _("The Cantingas River jump-off point under a bright blue sky"),
        "author": "Christian Jules Llave", "licence": "CC BY-SA 4.0",
        "source": "https://commons.wikimedia.org/wiki/File:CantingasRiver.jpg",
    },
    "g-coast": {
        "widths": [400, 800], "ratio": (4, 3),
        "alt": _("Aerial view of Sibuyan Island's coastline in a deep blue sea"),
        "author": "P199", "licence": "CC BY-SA 3.0",
        "source": "https://commons.wikimedia.org/wiki/File:Sibuyan_Island.JPG",
    },
    "t-guiting": {
        "widths": [600, 1200], "ratio": (16, 9),
        "alt": _("The jagged ridges of Mt. Guiting-Guiting seen from near the summit"),
        "author": "rjabalosIII", "licence": "CC BY 2.0",
        "source": "https://commons.wikimedia.org/wiki/File:Mount_Guiting-Guiting_DSC06614.jpg",
    },
    "t-cantingas": {
        "widths": [600, 1200], "ratio": (16, 9),
        "alt": _("Clear water running over boulders in the Cantingas River"),
        "author": "Carlojoseph14", "licence": "CC BY-SA 4.0",
        "source": "https://commons.wikimedia.org/wiki/File:Cantingas_River.jpg",
    },
    "s-ridge": {
        "widths": [300, 600], "ratio": (4, 3),
        "alt": _("A sea of clouds below the summit ridges of Mt. Guiting-Guiting"),
        "author": "Ray Santa Maria", "licence": "CC BY-SA 4.0",
        "source": "https://commons.wikimedia.org/wiki/File:Mount_Guiting_Guiting_5.jpg",
    },
    "s-forest": {
        "widths": [300, 600], "ratio": (4, 3),
        "alt": _("Unbroken forest on the slopes of Mt. Guiting-Guiting, with the sea beyond"),
        "author": ANDROKOY[0], "licence": ANDROKOY[1],
        "source": "https://commons.wikimedia.org/wiki/File:Guiting-guiting_5.jpg",
    },
    "s-nepenthes": {
        "widths": [360], "ratio": (3, 4),
        "alt": _("A red-speckled pitcher of Nepenthes sibuyanensis, found only on Sibuyan"),
        "author": "Alastair Robinson (Attenboroughii)", "licence": "CC BY 3.0",
        "source": "https://commons.wikimedia.org/wiki/File:Nepenthes_sibuyanensis_ASR_062007_guiting2_sibuyan.jpg",
    },
}


def photo(key):
    """Template-ready dict: src, srcset, width/height, alt and credit."""
    meta = PHOTOS[key]
    widths = meta["widths"]
    rw, rh = meta["ratio"]
    url = lambda w: static(f"img/photos/{key}-{w}.webp")  # noqa: E731
    return {
        "key": key,
        "src": url(widths[-1]),
        "srcset": ", ".join(f"{url(w)} {w}w" for w in widths),
        "width": widths[-1],
        "height": round(widths[-1] * rh / rw),
        "alt": meta["alt"],
        "credit": f"{meta['author']}, {meta['licence']}",
        "source": meta["source"],
    }
