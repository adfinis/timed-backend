from datetime import date, timedelta
from dateutil import rrule
from django.db.models import Sum
from typing import Union

from timed.employment.models import Employment, EmploymentChange, PublicHoliday,OvertimeCredit
from timed.tracking.models import Absence, Report


def get_schedule(start,end,employment: Union[Employment, EmploymentChange]):

    """
    Obtaining weekly working days, holidays, overtime credit, 
    reported working time and absences

    :params start: working starting time on a given day 
    :params end : working end time of a given day 
    :employment : Employement or EmploymentChange object
    """
   
    if isinstance(employment, Employment):
        location = employment.location
        user_id = employment.user.id
    elif isinstance(employment, EmploymentChange):
        location = employment.employment.location
        user_id = employment.employment.user.id

    # shorten time frame to employment
    start = max(start, employment.start_date)
    end = min(employment.end_date or date.today(), end)

    week_workdays = [int(day) - 1 for day in employment.location.workdays]
    workdays = rrule.rrule(
            rrule.DAILY, dtstart=start, until=end, byweekday=week_workdays
        ).count()
    
    # converting workdays as db expects 1 (Sunday) to 7 (Saturday)
    workdays_db = [
            # special case for Sunday
            int(day) == 7 and 1 or int(day) + 1
            for day in location.workdays
        ]
    holidays = PublicHoliday.objects.filter(
            location=location,
            date__gte=start,
            date__lte=end,
            date__week_day__in=workdays_db,
        ).count()
    
    overtime_credit_data = OvertimeCredit.objects.filter(
            user=user_id, date__gte=start, date__lte=end
        ).aggregate(total_duration=Sum("duration"))
    overtime_credit = overtime_credit_data["total_duration"] or timedelta()

    reported_worktime_data = Report.objects.filter(
            user=user_id, date__gte=start, date__lte=end
        ).aggregate(duration_total=Sum("duration"))
    reported_worktime = reported_worktime_data["duration_total"] or timedelta()

    absences = sum(
            [
                absence.calculate_duration(employment)
                for absence in Absence.objects.filter(
                    user=user_id, date__gte=start, date__lte=end
                ).select_related("absence_type")
            ],
            timedelta(),
        )

    return (workdays,holidays,overtime_credit,reported_worktime,absences)