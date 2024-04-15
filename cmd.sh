#!/bin/sh

# All parameters to the script are appended as arguments to `manage.py serve`

set -x

manage.py collectstatic --noinput

set -e

manage.py serve --static --port 8080 --req-queue-len "${HURRICANE_REQ_QUEUE_LEN:-250}" "$@"