from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from concerns.admin_views import analytics_view
from core import views as core_views

admin.site.site_header = "SibuyanConnect CMS"
admin.site.site_title = "SibuyanConnect CMS"
admin.site.index_title = "LGU content and concern management"

urlpatterns = [
    path("admin/analytics/", admin.site.admin_view(analytics_view), name="admin-analytics"),
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("services/", include("services.urls")),
    path("programs/", include("programs.urls")),
    path("concerns/", include("concerns.urls")),
    path("news/", include("news.urls")),
    path("transport/", include("transport.urls")),
    path("emergency/", include("emergency.urls")),
    path("assistant/", include("assistant.urls")),
    path("tourism/", include("tourism.urls")),
    path("transparency/", include("civic.urls")),
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("accounts/signup/", core_views.signup, name="signup"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
