"""Root URL mapping."""

from django.conf.urls import include, url
from django.contrib import admin
from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token

urlpatterns = [
    url(r"^admin/", admin.site.urls),
    url(r"^api/v1/auth/login", obtain_jwt_token, name="login"),
    url(r"^api/v1/auth/refresh", refresh_jwt_token, name="refresh"),
    url(r"^api/v1/", include("timed.employment.urls")),
    url(r"^api/v1/", include("timed.projects.urls")),
    url(r"^api/v1/", include("timed.tracking.urls")),
    url(r"^api/v1/", include("timed.reports.urls")),
    url(r"^api/v1/", include("timed.subscription.urls")),
]
