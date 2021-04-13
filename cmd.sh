#!/bin/sh

sed -i \
    -e 's/max-requests = .*/max-requests = '"${UWSGI_MAX_REQUESTS}"'/g' "${UWSGI_INI}" \
    -e 's/harakiri = .*/harakiri = '"${UWSGI_HARAKIRI}"'/g' "${UWSGI_INI}" \
    -e 's/processes = .*/processes = '"${UWSGI_PROCESSES}"'/g' "${UWSGI_INI}"

wait-for-it.sh "${DJANGO_DATABASE_HOST}":"${DJANGO_DATABASE_PORT}" -t "${WAITFORIT_TIMEOUT}" -- \
    ./manage.py migrate --no-input && \
    ./manage.py collectstatic --noinput && \
    uwsgi
