from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("town/", views.set_town, name="set-town"),
    path("language/", views.set_language, name="set-language"),
    path("privacy/", views.privacy, name="privacy"),
    path("offline/", views.offline, name="offline"),
    path("manifest.webmanifest", views.manifest, name="manifest"),
    path("sw.js", views.service_worker, name="service-worker"),
]
