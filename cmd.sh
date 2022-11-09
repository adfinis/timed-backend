#!/bin/sh

# All parameters to the script are appended as arguments to `manage.py serve`

set -x

poetry run python manage.py manage.py collectstatic --noinput

set -e

wait-for-it.sh "${DJANGO_DATABASE_HOST}":"${DJANGO_DATABASE_PORT}" -t "${WAITFORIT_TIMEOUT}"
poetry run python manage.py migrate --no-input
poetry run python manage.py serve --static --port 80 --req-queue-len "${HURRICANE_REQ_QUEUE_LEN:-250}" "$@"
