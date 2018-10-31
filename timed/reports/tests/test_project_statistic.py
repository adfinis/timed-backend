from datetime import timedelta

from django.urls import reverse

from timed.tracking.factories import ReportFactory


def test_project_statistic_list(auth_client, django_assert_num_queries):
    report = ReportFactory.create(duration=timedelta(hours=1))
    ReportFactory.create(duration=timedelta(hours=2), task=report.task)
    report2 = ReportFactory.create(duration=timedelta(hours=4))

    url = reverse('project-statistic-list')
    with django_assert_num_queries(5):
        result = auth_client.get(url, data={
            'ordering': 'duration',
            'include': 'project,project.customer'
        })
    assert result.status_code == 200

    json = result.json()
    expected_json = [
        {
            'type': 'project-statistics',
            'id': str(report.task.project.id),
            'attributes': {
                'duration': '03:00:00'
            },
            'relationships': {
                'project': {
                    'data': {
                        'id': str(report.task.project.id),
                        'type': 'projects'
                    }
                }
            }
        },
        {
            'type': 'project-statistics',
            'id': str(report2.task.project.id),
            'attributes': {
                'duration': '04:00:00'
            },
            'relationships': {
                'project': {
                    'data': {
                        'id': str(report2.task.project.id),
                        'type': 'projects'
                    }
                }
            }
        }
    ]

    assert json['data'] == expected_json
    assert len(json['included']) == 4
    assert json['meta']['total-time'] == '07:00:00'
