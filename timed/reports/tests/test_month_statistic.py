from datetime import date, timedelta

from django.urls import reverse

from timed.tracking.factories import ReportFactory


def test_month_statistic_list(auth_client):
    ReportFactory.create(duration=timedelta(hours=1), date=date(2016, 1, 1))
    ReportFactory.create(duration=timedelta(hours=1), date=date(2015, 12, 4))
    ReportFactory.create(duration=timedelta(hours=2), date=date(2015, 12, 31))

    url = reverse("month-statistic-list")
    result = auth_client.get(url, data={"ordering": "year,month"})
    assert result.status_code == 200

    json = result.json()
    expected_json = [
        {
            "type": "month-statistics",
            "id": "2015-12",
            "attributes": {"year": 2015, "month": 12, "duration": "03:00:00"},
        },
        {
            "type": "month-statistics",
            "id": "2016-1",
            "attributes": {"year": 2016, "month": 1, "duration": "01:00:00"},
        },
    ]

    assert json["data"] == expected_json
    assert json["meta"]["total-time"] == "04:00:00"
