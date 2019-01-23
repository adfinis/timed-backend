FROM python:3.6

WORKDIR /app

RUN wget https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh -P /usr/local/bin \
&& chmod +x /usr/local/bin/wait-for-it.sh

RUN apt-get update && apt-get install -y --no-install-recommends \
  libldap2-dev \
  libsasl2-dev \
&& rm -rf /var/lib/apt/lists/* \
&& mkdir -p /app

ARG REQUIREMENTS=requirements.txt

ENV DJANGO_SETTINGS_MODULE timed.settings
ENV STATIC_ROOT /var/www/static
ENV UWSGI_INI /app/uwsgi.ini

COPY requirements.txt requirements-dev.txt /app/
RUN pip install --upgrade --no-cache-dir --requirement $REQUIREMENTS --disable-pip-version-check

COPY . /app

RUN mkdir -p /var/www/static \
&& ENV=docker ./manage.py collectstatic --noinput

EXPOSE 80
CMD /bin/sh -c "wait-for-it.sh $DJANGO_DATABASE_HOST:$DJANGO_DATABASE_PORT -- ./manage.py migrate && uwsgi"
