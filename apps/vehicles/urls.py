from django.urls import path
from . import views

app_name = "vehicles"

urlpatterns = [
    path("", views.vehicle_list_view, name="vehicle_list"),
    path("add/", views.vehicle_create_view, name="vehicle_create"),
    path("<int:pk>/", views.vehicle_detail_view, name="vehicle_detail"),

    path("appointments/", views.appointment_list_view, name="appointment_list"),
    path("appointments/book/", views.appointment_create_view, name="appointment_create"),
    path("appointments/<int:pk>/confirm/", views.appointment_confirm_view, name="appointment_confirm"),
    path("appointments/<int:pk>/cancel/", views.appointment_cancel_view, name="appointment_cancel"),
]
