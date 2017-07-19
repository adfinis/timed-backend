"""Tests for the activities endpoint."""

from datetime import datetime

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from pytz import timezone
from rest_framework.status import (HTTP_200_OK, HTTP_201_CREATED,
                                   HTTP_204_NO_CONTENT, HTTP_401_UNAUTHORIZED)

from timed.jsonapi_test_case import JSONAPITestCase
from timed.tracking.factories import ActivityBlockFactory, ActivityFactory


class ActivityTests(JSONAPITestCase):
    """Tests for the activities endpoint."""

    def setUp(self):
        """Set the environment for the tests up."""
        super().setUp()

        other_user = User.objects.create_user(
            username='test',
            password='123qweasd'
        )

        self.activities = ActivityFactory.create_batch(
            20,
            user=self.user
        )

        for activity in self.activities:
            ActivityBlockFactory.create_batch(5, activity=activity)

        ActivityFactory.create_batch(
            10,
            user=other_user
        )

    def test_activity_list(self):
        """Should respond with a list of activities filtered by user."""
        url = reverse('activity-list')

        noauth_res = self.noauth_client.get(url)
        res        = self.client.get(url)

        assert noauth_res.status_code == HTTP_401_UNAUTHORIZED
        assert res.status_code == HTTP_200_OK

        result = self.result(res)

        assert len(result['data']) == len(self.activities)

    def test_activity_detail(self):
        """Should respond with a single activity."""
        activity = self.activities[0]

        url = reverse('activity-detail', args=[
            activity.id
        ])

        noauth_res = self.noauth_client.get(url)
        res        = self.client.get(url)

        assert noauth_res.status_code == HTTP_401_UNAUTHORIZED
        assert res.status_code == HTTP_200_OK

    def test_activity_create(self):
        """Should create a new activity and automatically set the user."""
        task = self.activities[0].task

        data = {
            'data': {
                'type': 'activities',
                'id': None,
                'attributes': {
                    'comment': 'Test activity'
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

        url = reverse('activity-list')

        noauth_res = self.noauth_client.post(url, data)
        res        = self.client.post(url, data)

        assert noauth_res.status_code == HTTP_401_UNAUTHORIZED
        assert res.status_code == HTTP_201_CREATED

        result = self.result(res)

        assert (
            int(result['data']['relationships']['user']['data']['id']) ==
            int(self.user.id)
        )

    def test_activity_update(self):
        """Should update an existing activity."""
        activity = self.activities[0]

        data = {
            'data': {
                'type': 'activities',
                'id': activity.id,
                'attributes': {
                    'comment': 'Test activity 2'
                }
            }
        }

        url = reverse('activity-detail', args=[
            activity.id
        ])

        noauth_res = self.noauth_client.patch(url, data)
        res        = self.client.patch(url, data)

        assert noauth_res.status_code == HTTP_401_UNAUTHORIZED
        assert res.status_code == HTTP_200_OK

        result = self.result(res)

        assert (
            result['data']['attributes']['comment'] ==
            data['data']['attributes']['comment']
        )

    def test_activity_delete(self):
        """Should delete an activity."""
        activity = self.activities[0]

        url = reverse('activity-detail', args=[
            activity.id
        ])

        noauth_res = self.noauth_client.delete(url)
        res        = self.client.delete(url)

        assert noauth_res.status_code == HTTP_401_UNAUTHORIZED
        assert res.status_code == HTTP_204_NO_CONTENT

    def test_activity_list_filter_active(self):
        """Should respond with a list of active activities."""
        activity = self.activities[0]
        block    = ActivityBlockFactory.create(activity=activity)

        block.to_datetime = None
        block.save()

        url = reverse('activity-list')

        res = self.client.get('{0}?active=true'.format(url))

        result = self.result(res)

        assert len(result['data']) == 1

        assert int(result['data'][0]['id']) == int(activity.id)

    def test_activity_list_filter_day(self):
        """Should respond with a list of activities starting today."""
        now      = datetime.now(timezone('Europe/Zurich'))
        activity = self.activities[0]

        activity.start_datetime = now
        activity.save()

        url = reverse('activity-list')

        res = self.client.get('{0}?day={1}'.format(
            url,
            now.strftime('%Y-%m-%d')
        ))

        result = self.result(res)

        assert len(result['data']) >= 1

        assert any([
            int(data['id']) == activity.id
            for data
            in result['data']
        ])

    def test_activity_list_filter_recent(self):
        """Should respond with a list of recent activities."""
        url = reverse('activity-list')

        res = self.client.get('{0}?recent=true'.format(url))
        result = self.result(res)

        assert len(result['data']) >= 1
        assert len(result['data']) <= 10

        def get_task(entry):
            return entry['relationships']['task']['data']['id']

        # Each task should be unique
        tasks = list(map(get_task, result['data']))

        assert len(tasks) == len(set(tasks))

    def test_activity_create_no_task(self):
        """Should create a new activity without a task."""
        data = {
            'data': {
                'type': 'activities',
                'id': None,
                'attributes': {
                    'comment': 'Test activity'
                },
                'relationships': {
                    'task': {
                        'data': None
                    }
                }
            }
        }

        url = reverse('activity-list')

        noauth_res = self.noauth_client.post(url, data)
        res        = self.client.post(url, data)

        assert noauth_res.status_code == HTTP_401_UNAUTHORIZED
        assert res.status_code == HTTP_201_CREATED

        result = self.result(res)

        assert result['data']['relationships']['task']['data'] is None
