import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Count, Max
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_POST

from civic.models import Official, PublicDocument
from emergency.models import Hotline
from news.models import Post
from programs.models import Program
from tourism.showcase import discover_tiles
from services.models import Service
from transport.models import Trip

from .middleware import LANG_COOKIE, LANG_SESSION_KEY
from .models import Municipality
from .photos import photo
from .town import TOWN_SESSION_KEY, get_current_town


def _safe_next(request, fallback="home"):
    nxt = request.POST.get("next") or request.GET.get("next")
    if nxt and url_has_allowed_host_and_scheme(nxt, {request.get_host()}, request.is_secure()):
        return nxt
    return reverse(fallback)


SERVICE_TILES = [
    # (category slug, icon id, title, one-line description)
    ("civil-registry", "registry", _lazy("Civil Registry"), _lazy("Birth, marriage and death records")),
    ("permits", "permit", _lazy("Permits & Clearances"), _lazy("Business, building, cedula, clearances")),
    ("social-welfare", "welfare", _lazy("Social Welfare"), _lazy("Assistance, senior citizen and PWD IDs")),
    ("health", "health", _lazy("Health"), _lazy("Rural health unit, vaccines, check-ups")),
    ("agriculture", "sprout", _lazy("Agriculture"), _lazy("RSBSA, farm and fisheries support")),
]


# "Did you know?" facts. Each was checked against the cited source (October 2026).
ISLAND_FACTS = [
    ("pitcher", _lazy("Home of Nepenthes sibuyanensis"),
     _lazy("A pitcher plant that grows wild nowhere on Earth except Sibuyan."),
     "Wikipedia: Nepenthes sibuyanensis (Nerz, 1998)", "https://en.wikipedia.org/wiki/Nepenthes_sibuyanensis"),
    ("trees", _lazy("1,551 trees in one hectare"),
     _lazy("The densest forest ever recorded in the Philippines, with 54 tree species found nowhere else."),
     "Wikipedia: Sibuyan; Mount Guiting-Guiting", "https://en.wikipedia.org/wiki/Sibuyan"),
    ("mountain", _lazy("A protected natural park"),
     _lazy("Mt. Guiting-Guiting (2,058 m) and its forests have been a protected Natural Park since 1996."),
     "Proclamation No. 746, s. 1996", "https://lawphil.net/executive/proc/proc1996/proc_746_1996.html"),
    ("drop", _lazy("Among the cleanest rivers"),
     _lazy("The government has called Cantingas River the cleanest inland body of water in the Philippines."),
     "Philippine Daily Inquirer", "https://newsinfo.inquirer.net/639773/campaign-on-to-save-cleanest-river-in-ph"),
]


def _hero_slides():
    """Extra hero photos for the desktop crossfade; JS loads them only when appropriate."""
    slides = []
    for key in ("hero-coast", "hero-cantingas"):
        p = photo(key)
        slides.append({"srcset": p["srcset"], "src": p["src"], "alt": str(p["alt"]),
                       "credit": p["credit"], "source": p["source"]})
    return json.dumps(slides)


def _distinct_titles(documents, limit=4):
    """With 'All towns', each LGU may post a similar notice; show each title once."""
    seen, picked = set(), []
    for doc in documents[:limit * 4]:
        if doc.title not in seen:
            seen.add(doc.title)
            picked.append(doc)
        if len(picked) == limit:
            break
    return picked


def home(request):
    town = get_current_town(request)
    services = Service.objects.filter(is_published=True).for_town(town)
    counts = dict(services.values("category__slug").annotate(n=Count("id")).values_list("category__slug", "n"))
    tiles = [
        {"url": f"{reverse('services:list')}?category={slug}", "icon": icon, "title": title,
         "text": text, "count": counts.get(slug, 0)}
        for slug, icon, title, text in SERVICE_TILES
    ]
    tiles.append({"url": reverse("services:list"), "icon": "grid", "title": _("All services"),
                  "text": _("Every service, with requirements and fees"), "count": services.count()})

    posts = Post.objects.published().for_town(town).select_related("municipality")
    documents = PublicDocument.objects.for_town(town).select_related("municipality")
    mayors = Official.objects.filter(position="Municipal Mayor").select_related("municipality")
    if town:
        mayors = mayors.filter(municipality=town)
    context = {
        "hero": photo("hero-guiting"),
        "hero_m": photo("hero-guiting-m"),
        "hero_slides": _hero_slides(),
        "discover": discover_tiles(),
        "facts": ISLAND_FACTS,
        "tiles": tiles,
        "mayors": mayors,
        "trips_today": Trip.objects.for_town(town)
        .filter(departure_date=timezone.localdate())
        .select_related("route")[:4],
        "hotlines": Hotline.objects.for_town(town).order_by("order", "agency")[:4],
        "programs": Program.objects.filter(is_published=True).for_town(town).order_by("-view_count", "name")[:3],
        "bids": _distinct_titles(documents.filter(kind=PublicDocument.Kind.PROCUREMENT)),
        "reports": _distinct_titles(documents.filter(kind=PublicDocument.Kind.BUDGET)),
        "latest_posts": posts[:3],
    }
    return render(request, "core/home.html", context)


def set_town(request):
    slug = request.GET.get("town") or request.POST.get("town") or ""
    if slug and Municipality.objects.filter(slug=slug).exists():
        request.session[TOWN_SESSION_KEY] = slug
    else:
        request.session.pop(TOWN_SESSION_KEY, None)
    return redirect(_safe_next(request))


@require_POST
def set_language(request):
    lang = request.POST.get("language")
    response = redirect(_safe_next(request))
    if lang in dict(settings.LANGUAGES):
        request.session[LANG_SESSION_KEY] = lang
        response.set_cookie(LANG_COOKIE, lang, max_age=365 * 24 * 3600, samesite="Lax")
    return response


def privacy(request):
    return render(request, "core/privacy.html")


def offline(request):
    return render(request, "core/offline.html")


@cache_control(max_age=86400)
def manifest(request):
    return render(request, "core/manifest.webmanifest", content_type="application/manifest+json")


@cache_control(no_cache=True)
def service_worker(request):
    """Served from the site root so its scope covers every page.

    The page list and cache version are rendered from the database, so the
    browser fetches a fresh copy of the offline pages whenever staff edit a
    service, a sailing or a hotline.
    """
    services = Service.objects.filter(is_published=True)
    stamps = [
        services.aggregate(m=Max("updated_at"))["m"],
        Trip.objects.aggregate(m=Max("updated_at"))["m"],
    ]
    version = "-".join(s.strftime("%Y%m%d%H%M%S") for s in stamps if s) or "1"
    version += f"-{Hotline.objects.count()}"
    offline_urls = [
        reverse("home"), reverse("services:list"), reverse("emergency:hub"),
        reverse("transport:board"), reverse("programs:list"), reverse("offline"),
    ] + [s.get_absolute_url() for s in services]
    return render(request, "core/sw.js", {"version": version, "offline_urls": json.dumps(offline_urls)},
                  content_type="application/javascript")


def signup(request):
    """Optional citizen account: lets residents see all their concerns in one place."""
    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, _("Your account was created."))
        return redirect("concerns:mine")
    return render(request, "registration/signup.html", {"form": form})
