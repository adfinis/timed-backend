#!/bin/sh

# All parameters to the script are appended as arguments to `manage.py serve`

set -x

./manage.py collectstatic --noinput

set -e

wait-for-it.sh "${DJANGO_DATABASE_HOST}":"${DJANGO_DATABASE_PORT}" -t "${WAITFORIT_TIMEOUT}"
./manage.py migrate --no-input
./manage.py serve --static --port 80 --req-queue-len "${HURRICANE_REQ_QUEUE_LEN:-250}" "$@"
