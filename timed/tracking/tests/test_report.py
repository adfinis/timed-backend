"""Tests for the reports endpoint."""

from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.duration import duration_string
from rest_framework.status import (HTTP_200_OK, HTTP_201_CREATED,
                                   HTTP_204_NO_CONTENT, HTTP_401_UNAUTHORIZED)

from timed.employment.factories import AbsenceTypeFactory, EmploymentFactory
from timed.jsonapi_test_case import JSONAPITestCase
from timed.projects.factories import TaskFactory
from timed.tracking.factories import AbsenceFactory, ReportFactory
from timed.tracking.models import Absence, Report


class ReportTests(JSONAPITestCase):
    """Tests for the reports endpoint."""

    def setUp(self):
        """Set the environment for the tests up."""
        super().setUp()

        other_user = User.objects.create_user(
            username='test',
            password='123qweasd'
        )

        self.reports = ReportFactory.create_batch(10, user=self.user)

        ReportFactory.create_batch(10, user=other_user)

    def test_report_list(self):
        """Should respond with a list of reports filtered by user."""
        url = reverse('report-list')

        noauth_res = self.noauth_client.get(url)
        user_res   = self.client.get(url)

        assert noauth_res.status_code == HTTP_401_UNAUTHORIZED
        assert user_res.status_code == HTTP_200_OK

        result = self.result(user_res)

        assert len(result['data']) == len(self.reports)

    def test_report_list_filter_recent(self):
        """Should respond with a list of recent reports."""
        url = reverse('report-list')

        res = self.client.get('{0}?recent=true'.format(url))
        result = self.result(res)

        assert len(result['data']) >= 1
        assert len(result['data']) <= 10

        def get_task(entry):
            return entry['relationships']['task']['data']['id']

        # Each task should be unique
        tasks = list(map(get_task, result['data']))

        assert len(tasks) == len(set(tasks))

    def test_report_detail(self):
        """Should respond with a single report."""
        report = self.reports[0]

        url = reverse('report-detail', args=[
            report.id
        ])

        noauth_res = self.noauth_client.get(url)
        user_res   = self.client.get(url)

        assert noauth_res.status_code == HTTP_401_UNAUTHORIZED
        assert user_res.status_code == HTTP_200_OK

    def test_report_create(self):
        """Should create a new report and automatically set the user."""
        task = TaskFactory.create()

        data = {
            'data': {
                'type': 'reports',
                'id': None,
                'attributes': {
                    'comment':  'foo',
                    'duration': '00:50:00',
                    'date': '2017-02-01'
                },
                'relationships': {
                    'task': {
                        'data': {
                            'type': 'tasks',
                            'id': task.id
                        }
                    },
                }
            }
        }

        url = reverse('report-list')

        noauth_res = self.noauth_client.post(url, data)
        user_res   = self.client.post(url, data)

        assert noauth_res.status_code == HTTP_401_UNAUTHORIZED
        assert user_res.status_code == HTTP_201_CREATED

        result = self.result(user_res)

        assert (
            int(result['data']['relationships']['user']['data']['id']) ==
            int(self.user.id)
        )

        assert (
            int(result['data']['relationships']['task']['data']['id']) ==
            int(data['data']['relationships']['task']['data']['id'])
        )

    def test_report_update(self):
        """Should update an existing report."""
        report = self.reports[0]

        task = TaskFactory.create()

        data = {
            'data': {
                'type': 'reports',
                'id': report.id,
                'attributes': {
                    'comment':  'foobar',
                    'duration': '01:00:00',
                    'date': '2017-02-04'
                },
                'relationships': {
                    'task': {
                        'data': {
                            'type': 'tasks',
                            'id': task.id
                        }
                    }
                }
            }
        }

        url = reverse('report-detail', args=[
            report.id
        ])

        noauth_res = self.noauth_client.patch(url, data)
        user_res   = self.client.patch(url, data)

        assert noauth_res.status_code == HTTP_401_UNAUTHORIZED
        assert user_res.status_code == HTTP_200_OK

        result = self.result(user_res)

        assert (
            result['data']['attributes']['comment'] ==
            data['data']['attributes']['comment']
        )

        assert (
            result['data']['attributes']['duration'] ==
            data['data']['attributes']['duration']
        )

        assert (
            result['data']['attributes']['date'] ==
            data['data']['attributes']['date']
        )

        assert (
            int(result['data']['relationships']['task']['data']['id']) ==
            int(data['data']['relationships']['task']['data']['id'])
        )

    def test_report_delete(self):
        """Should delete a report."""
        report = self.reports[0]

        url = reverse('report-detail', args=[
            report.id
        ])

        noauth_res = self.noauth_client.delete(url)
        user_res   = self.client.delete(url)

        assert noauth_res.status_code == HTTP_401_UNAUTHORIZED
        assert user_res.status_code == HTTP_204_NO_CONTENT

    def test_report_round_duration(self):
        """Should round the duration of a report to 15 minutes."""
        report = self.reports[0]

        report.duration = timedelta(hours=1, minutes=7)
        report.save()

        assert duration_string(report.duration) == '01:00:00'

        report.duration = timedelta(hours=1, minutes=8)
        report.save()

        assert duration_string(report.duration) == '01:15:00'

        report.duration = timedelta(hours=1, minutes=53)
        report.save()

        assert duration_string(report.duration) == '02:00:00'

    def test_absence_update_on_create_report(self):
        """Should update the absence after creating a new report."""
        task = TaskFactory.create()
        type = AbsenceTypeFactory.create(fill_worktime=True)
        day  = date(2017, 5, 3)

        employment = EmploymentFactory.create(user=self.user, start_date=day)

        absence = AbsenceFactory.create(user=self.user, date=day, type=type)

        Report.objects.create(
            user=self.user,
            date=day,
            task=task,
            duration=timedelta(hours=1)
        )

        assert (
            Absence.objects.get(pk=absence.pk).duration ==
            employment.worktime_per_day - timedelta(hours=1)
        )
