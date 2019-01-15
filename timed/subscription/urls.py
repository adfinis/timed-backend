from django.conf import settings
from rest_framework.routers import DefaultRouter

from . import views

r = DefaultRouter(trailing_slash=settings.APPEND_SLASH)

r.register(
    r"subscription-projects", views.SubscriptionProjectViewSet, "subscription-project"
)
r.register(r"subscription-packages", views.PackageViewSet, "subscription-package")
r.register(r"subscription-orders", views.OrderViewSet, "subscription-order")

urlpatterns = r.urls
