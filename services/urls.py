from django.urls import path

from . import views

app_name = "services"
urlpatterns = [
    path("", views.service_list, name="list"),
    # Must come before the detail route, which would otherwise read "checklist" as a slug.
    path("<int:pk>/checklist/", views.checklist, name="checklist"),
    path("<int:pk>/<slug:slug>/", views.service_detail, name="detail"),
]
