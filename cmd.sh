#!/bin/sh

GUNICORN_WORKERS="${GUNICORN_WORKERS:-8}"

set -x

./manage.py collectstatic --noinput

set -e

wait-for-it.sh "${DJANGO_DATABASE_HOST}":"${DJANGO_DATABASE_PORT}" -t "${WAITFORIT_TIMEOUT}"
./manage.py migrate --no-input
gunicorn --workers=$GUNICORN_WORKERS --bind=0.0.0.0:80 timed.wsgi:application
