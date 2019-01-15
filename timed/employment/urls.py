"""URL to view mapping for the employment app."""

from django.conf import settings
from rest_framework.routers import SimpleRouter

from timed.employment import views

r = SimpleRouter(trailing_slash=settings.APPEND_SLASH)

r.register(r"users", views.UserViewSet, "user")
r.register(r"employments", views.EmploymentViewSet, "employment")
r.register(r"locations", views.LocationViewSet, "location")
r.register(r"public-holidays", views.PublicHolidayViewSet, "public-holiday")
r.register(r"absence-types", views.AbsenceTypeViewSet, "absence-type")
r.register(r"overtime-credits", views.OvertimeCreditViewSet, "overtime-credit")
r.register(r"absence-credits", views.AbsenceCreditViewSet, "absence-credit")
r.register(r"worktime-balances", views.WorktimeBalanceViewSet, "worktime-balance")
r.register(r"absence-balances", views.AbsenceBalanceViewSet, "absence-balance")

urlpatterns = r.urls
