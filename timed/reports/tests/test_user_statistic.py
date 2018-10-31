from datetime import timedelta

from django.urls import reverse

from timed.tracking.factories import ReportFactory


def test_user_statistic_list(auth_client):
    user = auth_client.user
    ReportFactory.create(duration=timedelta(hours=1), user=user)
    ReportFactory.create(duration=timedelta(hours=2), user=user)
    report = ReportFactory.create(duration=timedelta(hours=2))

    url = reverse('user-statistic-list')
    result = auth_client.get(url, data={
        'ordering': 'duration',
        'include': 'user'
    })
    assert result.status_code == 200

    json = result.json()
    expected_json = [
        {
            'type': 'user-statistics',
            'id': str(report.user.id),
            'attributes': {
                'duration': '02:00:00'
            },
            'relationships': {
                'user': {
                    'data': {
                        'id': str(report.user.id),
                        'type': 'users'
                    }
                }
            }
        },
        {
            'type': 'user-statistics',
            'id': str(user.id),
            'attributes': {
                'duration': '03:00:00'
            },
            'relationships': {
                'user': {
                    'data': {
                        'id': str(user.id),
                        'type': 'users'
                    }
                }
            }
        }
    ]

    assert json['data'] == expected_json
    assert len(json['included']) == 2
    assert json['meta']['total-time'] == '05:00:00'
