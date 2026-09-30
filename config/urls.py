from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("auth/", include("apps.authentication.urls")),
    path("vehicles/", include("apps.vehicles.urls")),
    path("agent/", include("apps.ai_agent.urls")),
]
