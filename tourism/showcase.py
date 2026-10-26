"""Which photos illustrate which places. Places without a free photo yet get a
labelled placeholder (listed in CREDITS.md under "Needs photo")."""
from django.utils.translation import gettext_lazy as _

from core.photos import photo

# attraction slug -> header photo and small gallery (None = placeholder)
ATTRACTION_PHOTOS = {
    "mt-guiting-guiting": {"header": "t-guiting", "gallery": ["g-guiting", "s-ridge", "s-forest", "s-nepenthes"]},
    "cantingas-river": {"header": "t-cantingas", "gallery": ["g-cantingas"]},
    "lambingan-falls": {"header": None, "gallery": []},
    "cawa-cawa-falls": {"header": None, "gallery": []},
    "cresta-de-gallo": {"header": None, "gallery": []},
}

# Homepage "Discover Sibuyan" gallery, in bento order (the first tile is the large one).
DISCOVER = [
    ("mt-guiting-guiting", _("Mt. Guiting-Guiting"), "Magdiwang", "g-guiting"),
    ("cantingas-river", _("Cantingas River"), "San Fernando", "g-cantingas"),
    ("cawa-cawa-falls", _("Cawa-Cawa Falls"), "San Fernando", None),
    ("lambingan-falls", _("Lambingan Falls"), "Magdiwang", None),
    ("cresta-de-gallo", _("Cresta de Gallo"), "San Fernando", None),
    ("coast", _("The coastline"), _("All three towns"), "g-coast"),
]


def discover_tiles():
    return [
        {"anchor": slug, "name": name, "town": town, "photo": photo(key) if key else None}
        for slug, name, town, key in DISCOVER
    ]


def attraction_photos(slug):
    entry = ATTRACTION_PHOTOS.get(slug, {"header": None, "gallery": []})
    return {
        "header": photo(entry["header"]) if entry["header"] else None,
        "gallery": [photo(k) for k in entry["gallery"]],
    }
