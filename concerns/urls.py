from django.urls import path

from . import views

app_name = "concerns"
urlpatterns = [
    path("new/", views.new_concern, name="new"),
    path("track/", views.track, name="track"),
    path("mine/", views.my_concerns, name="mine"),
    path("t/<str:ticket_number>/<str:token>/", views.ticket, name="ticket"),
]
