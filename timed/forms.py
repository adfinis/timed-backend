from datetime import timedelta

from django.core.exceptions import ValidationError
from django.forms.fields import FloatField
from django.utils.translation import gettext_lazy as _


class DurationInHoursField(FloatField):
    """Field representing duration as float hours."""

    def _get_hours(self, value):
        return value.total_seconds() / 3600

    def prepare_value(self, value):
        if isinstance(value, timedelta):
            return self._get_hours(value)
        return value

    def to_python(self, value):
        value = super().to_python(value)
        if value is None:
            return value

        return timedelta(seconds=value * 3600)

    def validate(self, value):
        if value in self.empty_values:
            return

        if not isinstance(value, timedelta):
            raise ValidationError(_("Enter a datetime.timedelta"))

        super().validate(self._get_hours(value))
