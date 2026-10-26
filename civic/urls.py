from django.urls import path

from . import views

app_name = "civic"
urlpatterns = [
    path("", views.transparency, name="transparency"),
]
