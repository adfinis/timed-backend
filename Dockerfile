FROM python:3.9

WORKDIR /app

RUN wget https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh -P /usr/local/bin \
  && chmod +x /usr/local/bin/wait-for-it.sh

RUN apt-get update && apt-get install -y --no-install-recommends \
  libpq-dev \
  && rm -rf /var/lib/apt/lists/* \
  && mkdir -p /app

ENV DJANGO_SETTINGS_MODULE timed.settings
ENV STATIC_ROOT /var/www/static
ENV WAITFORIT_TIMEOUT 0

ENV HURRICANE_REQ_QUEUE_LEN 250

RUN pip install -U poetry

ARG INSTALL_DEV_DEPENDENCIES=false
COPY pyproject.toml poetry.lock /app/
RUN if [ "$INSTALL_DEV_DEPENDENCIES" = "true" ]; then poetry install; else poetry install --no-dev; fi

COPY . /app

RUN mkdir -p /var/www/static

EXPOSE 80
CMD ./cmd.sh
