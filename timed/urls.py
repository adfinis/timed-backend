"""Root URL mapping."""

from django.contrib import admin
from django.urls import include, re_path

urlpatterns = [
    re_path(r"^admin/", admin.site.urls),
    re_path(r"^api/v1/", include("timed.employment.urls")),
    re_path(r"^api/v1/", include("timed.projects.urls")),
    re_path(r"^api/v1/", include("timed.tracking.urls")),
    re_path(r"^api/v1/", include("timed.reports.urls")),
    re_path(r"^api/v1/", include("timed.subscription.urls")),
    re_path(r"^oidc/", include("mozilla_django_oidc.urls")),
    re_path(r"^prometheus/", include("django_prometheus.urls")),
]
