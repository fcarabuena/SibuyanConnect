from django.urls import path

from . import views

app_name = "tourism"
urlpatterns = [
    path("", views.attractions, name="attractions"),
]
