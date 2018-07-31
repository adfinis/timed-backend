FROM python:3.6

RUN apt-get update && apt-get install -y --no-install-recommends \
  libldap2-dev \
  libsasl2-dev \
&& rm -rf /var/lib/apt/lists/*

ENV DJANGO_SETTINGS_MODULE timed.settings
ENV STATIC_ROOT /var/www/static
ENV UWSGI_INI /app/uwsgi.ini

COPY . /app
WORKDIR /app

RUN make install

RUN mkdir -p /var/www/static \
&& ENV=docker ./manage.py collectstatic --noinput

EXPOSE 80
CMD ["uwsgi"]
