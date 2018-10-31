from datetime import timedelta

from django.urls import reverse

from timed.tracking.factories import ReportFactory


def test_customer_statistic_list(auth_client, django_assert_num_queries):
    report = ReportFactory.create(duration=timedelta(hours=1))
    ReportFactory.create(duration=timedelta(hours=2), task=report.task)
    report2 = ReportFactory.create(duration=timedelta(hours=4))

    url = reverse('customer-statistic-list')
    with django_assert_num_queries(4):
        result = auth_client.get(url, data={
            'ordering': 'duration',
            'include': 'customer'
        })
    assert result.status_code == 200

    json = result.json()
    expected_data = [
        {
            'type': 'customer-statistics',
            'id': str(report.task.project.customer.id),
            'attributes': {
                'duration': '03:00:00'
            },
            'relationships': {
                'customer': {
                    'data': {
                        'id': str(report.task.project.customer.id),
                        'type': 'customers'
                    }
                }
            }
        },
        {
            'type': 'customer-statistics',
            'id': str(report2.task.project.customer.id),
            'attributes': {
                'duration': '04:00:00'
            },
            'relationships': {
                'customer': {
                    'data': {
                        'id': str(report2.task.project.customer.id),
                        'type': 'customers'
                    }
                }
            }
        }
    ]

    assert json['data'] == expected_data
    assert len(json['included']) == 2
    assert json['meta']['total-time'] == '07:00:00'


def test_customer_statistic_detail(auth_client, django_assert_num_queries):
    report = ReportFactory.create(duration=timedelta(hours=1))

    url = reverse('customer-statistic-detail',
                  args=[report.task.project.customer.id])
    with django_assert_num_queries(3):
        result = auth_client.get(url, data={
            'ordering': 'duration',
            'include': 'customer'
        })
    assert result.status_code == 200
    json = result.json()
    assert json['data']['attributes']['duration'] == '01:00:00'
