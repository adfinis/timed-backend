from datetime import date, timedelta

from django.urls import reverse

from timed.tracking.factories import ReportFactory


def test_year_statistic_list(internal_employee_client):
    ReportFactory.create(duration=timedelta(hours=1), date=date(2017, 1, 1))
    ReportFactory.create(duration=timedelta(hours=1), date=date(2015, 2, 28))
    ReportFactory.create(duration=timedelta(hours=1), date=date(2015, 12, 31))

    url = reverse("year-statistic-list")
    result = internal_employee_client.get(url, data={"ordering": "year"})
    assert result.status_code == 200

    json = result.json()
    expected_json = [
        {
            "type": "year-statistics",
            "id": "2015",
            "attributes": {"year": 2015, "duration": "02:00:00"},
        },
        {
            "type": "year-statistics",
            "id": "2017",
            "attributes": {"year": 2017, "duration": "01:00:00"},
        },
    ]

    assert json["data"] == expected_json
    assert json["meta"]["total-time"] == "03:00:00"


def test_year_statistic_detail(internal_employee_client):
    ReportFactory.create(duration=timedelta(hours=1), date=date(2015, 2, 28))
    ReportFactory.create(duration=timedelta(hours=1), date=date(2015, 12, 31))

    url = reverse("year-statistic-detail", args=[2015])
    result = internal_employee_client.get(url, data={"ordering": "year"})
    assert result.status_code == 200
    json = result.json()
    assert json["data"]["attributes"]["duration"] == "02:00:00"
