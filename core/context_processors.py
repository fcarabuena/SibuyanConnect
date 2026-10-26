from django.conf import settings

from emergency.models import Hotline

from .models import Alert, Municipality
from .town import get_current_town


def site_context(request):
    if request.path.startswith("/admin/"):
        return {}
    town = get_current_town(request)
    severity = {Alert.Level.DANGER: 0, Alert.Level.WARNING: 1, Alert.Level.INFO: 2}
    alerts = sorted(Alert.objects.live().for_town(town).select_related("municipality")[:6],
                    key=lambda a: (severity.get(a.level, 3), -a.starts_at.timestamp()))
    return {
        "towns": Municipality.objects.all(),
        "current_town": town,
        "live_alerts": alerts,
        "footer_hotlines": Hotline.objects.for_town(town).order_by("order", "agency")[:4],
        "site_languages": settings.LANGUAGES,
        "weather_lat": settings.WEATHER_LAT,
        "weather_lon": settings.WEATHER_LON,
    }
