FROM python:3.11-alpine AS base

RUN apk update --no-cache && apk upgrade --no-cache && apk add shadow --no-cache && useradd -m -r -u 1001 timed && apk del shadow && rm -rf /var/cache/apk/*

RUN mkdir -p /var/www/static && chown timed:timed /var/www/static

COPY manage.py /usr/local/bin

ENV DJANGO_SETTINGS_MODULE=timed.settings \
  PYTHONUNBUFFERED=1 \
  STATIC_ROOT=/var/www/static \
  HURRICANE_REQ_QUEUE_LEN=200

EXPOSE 8080

FROM base AS build

WORKDIR /app

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONDONTWRITEBYTECODE=1 \
    # pip:
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    # poetry:
    POETRY_NO_INTERACTION=1

RUN pip install -U poetry

COPY . ./

FROM build as build-prod

WORKDIR /app

RUN poetry build -f wheel && mv ./dist/*.whl /tmp/

FROM build as dev

WORKDIR /app

RUN apk update --no-cache && \
 apk add gcc python3-dev musl-dev linux-headers wait4ports && \
 poetry config virtualenvs.create false && poetry install && \
 apk del gcc python3-dev musl-dev linux-headers --no-cache && \
 chmod 777 /var/www/static

USER 1001

CMD ["sh", "-c", "wait4ports -s 15 tcp://${DJANGO_DATABASE_HOST:-db}:${DJANGO_DATABASE_PORT:-5432}; manage.py migrate --no-input && ./cmd.sh --autoreload --static"]

FROM base as prod

COPY --from=build-prod /tmp/*.whl /tmp/

COPY cmd.sh /usr/local/bin

RUN apk add gcc python3-dev musl-dev linux-headers --no-cache && \
 pip install /tmp/*.whl --no-cache-dir && rm /tmp/*.whl && \
 apk del gcc python3-dev musl-dev linux-headers --no-cache

USER 1001

CMD ["cmd.sh"]