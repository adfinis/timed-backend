#!/bin/sh

# All parameters to the script are appended as arguments to `manage.py serve`

set -x

manage.py collectstatic --noinput

set -e

manage.py migrate --no-input
manage.py serve --static --port 80 --req-queue-len "${HURRICANE_REQ_QUEUE_LEN:-250}" "$@"