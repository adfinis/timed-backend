from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from djmoney.models.fields import MoneyField


class Package(models.Model):
    """Representing a subscription package."""

    billing_type = models.ForeignKey(
        "projects.BillingType",
        on_delete=models.CASCADE,
        null=True,
        related_name="packages",
    )
    """
    This field has been added later so there might be old entries with null
    hence null=True. However blank=True is not set as it is required to set
    for new packages.
    """

    duration = models.DurationField()
    price = MoneyField(max_digits=7, decimal_places=2, default_currency="CHF")


class Order(models.Model):
    """Order of customer for specific amount of hours."""

    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="orders"
    )
    duration = models.DurationField()
    ordered = models.DateTimeField(default=timezone.now)
    acknowledged = models.BooleanField(default=False)
    confirmedby = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders_confirmed",
    )


class CustomerPassword(models.Model):
    """
    Password per customer used for login into SySupport portal.

    Password are only hashed with md5. This model will be obsolete
    once customer center will go live.
    """

    customer = models.OneToOneField("projects.Customer", on_delete=models.CASCADE)
    password = models.CharField(_("password"), max_length=128, null=True, blank=True)
