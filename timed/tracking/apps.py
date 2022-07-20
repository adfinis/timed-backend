"""Configuration for tracking app."""

from django.apps import AppConfig


class TrackingConfig(AppConfig):
    """App configuration for tracking app."""

    name = "timed.tracking"
    label = "tracking"

    def ready(self):
        # Implicitly connect signal handlers decorated with @receiver.
        from . import signals  # noqa: F401
