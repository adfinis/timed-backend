"""Basic model and field classes to be used in all apps."""

from django.utils.translation import gettext_lazy as _
from multiselectfield import MultiSelectField
from multiselectfield.utils import get_max_length


class WeekdaysField(MultiSelectField):
    """Multi select field using weekdays as choices.

    Stores weekdays as comma-separated values in database as
    iso week day (MON = 1, SUN = 7).
    """

    MO, TU, WE, TH, FR, SA, SU = range(1, 8)

    WEEKDAYS = (
        (MO, _("Monday")),
        (TU, _("Tuesday")),
        (WE, _("Wednesday")),
        (TH, _("Thursday")),
        (FR, _("Friday")),
        (SA, _("Saturday")),
        (SU, _("Sunday")),
    )

    def __init__(self, *args, **kwargs):
        """Initialize multi select with choices weekdays."""
        kwargs["choices"] = self.WEEKDAYS
        kwargs["max_length"] = get_max_length(self.WEEKDAYS, None)
        super().__init__(*args, **kwargs)
