from .models import Municipality

TOWN_SESSION_KEY = "town"


def get_current_town(request):
    """The town picked in the switcher, or None for 'All Sibuyan'."""
    if not hasattr(request, "_current_town"):
        slug = request.session.get(TOWN_SESSION_KEY)
        request._current_town = Municipality.objects.filter(slug=slug).first() if slug else None
    return request._current_town
