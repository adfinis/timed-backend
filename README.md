# Timed Backend

[![Build Status](https://travis-ci.org/adfinis-sygroup/timed-backend.svg?branch=master)](https://travis-ci.org/adfinis-sygroup/timed-backend)
[![Codecov](https://codecov.io/gh/adfinis-sygroup/timed-backend/branch/master/graph/badge.svg)](https://codecov.io/gh/adfinis-sygroup/timed-backend)
[![Pyup](https://pyup.io/repos/github/adfinis-sygroup/timed-backend/shield.svg)](https://pyup.io/account/repos/github/adfinis-sygroup/timed-backend/)
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/adfinis-sygroup/cookiecutter-django-json-api)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

Timed timetracking software REST API built with Django

## Installation

**Requirements**

- docker
- docker-compose

After installing and configuring those requirements, you should be able to run the following
commands to complete the installation:

```bash
make start
```

You can now access the API at http://localhost:8000/api/v1 and the admin interface at http://localhost:8000/admin/

For end user interface have a look at our [Timed Frontend](https://github.com/adfinis-sygroup/timed-frontend) project.

## Configuration

Following options can be set as environment variables to configure Timed backend in documented [format](https://github.com/joke2k/django-environ#supported-types)
according to type.

| Parameter                           | Description                                           | Default             |
| ----------------------------------- | ----------------------------------------------------- | ------------------- |
| `DJANGO_ENV_FILE`                   | Path to setup environment vars in a file              | .env                |
| `DJANGO_DEBUG`                      | Boolean that turns on/off debug mode                  | False               |
| `DJANGO_SECRET_KEY`                 | Secret key for cryptographic signing                  | not set (required)  |
| `DJANGO_ALLOWED_HOSTS`              | List of hosts representing the host/domain names      | not set (required)  |
| `DJANGO_HOST_PROTOCOL`              | Protocol host is running on (http or https)           | http                |
| `DJANGO_HOST_DOMAIN`                | Main host name server is reachable on                 | not set (required)  |
| `DJANGO_DATABASE_NAME`              | Database name                                         | timed               |
| `DJANGO_DATABASE_USER`              | Database username                                     | timed               |
| `DJANGO_DATABASE_HOST`              | Database hostname                                     | localhost           |
| `DJANGO_DATABASE_PORT`              | Database port                                         | 5432                |
| `DJANGO_AUTH_LDAP_ENABLED`          | Enable LDAP authentication                            | False               |
| `DJANGO_AUTH_LDAP_SERVER_URI`       | uri of LDAP server                                    | not set             |
| `DJANGO_AUTH_LDAP_BIND_DN`          | distinguished name to use when binding to LDAP server | not set             |
| `DJANGO_AUTH_LDAP_PASSWORD`         | password to use with DJANGO_AUTH_LDAP_BIND_DN         | not set             |
| `DJANGO_AUTH_LDAP_USER_DN_TEMPLATE` | template to distinguish user’s username               | not set             |
| `EMAIL_URL`                         | Uri of email server                                   | smtp://localhost:25 |
| `DJANGO_DEFAULT_FROM_EMAIL`         | Default email address to use for various responses    | webmaster@localhost |
| `DJANGO_SERVER_EMAIL`               | Email address error messages are sent from            | root@localhost      |
| `DJANGO_ADMINS`                     | List of people who get error notifications            | not set             |
| `DJANGO_WORK_REPORT_PATH`           | Path of custom work report template                   | not set             |

## Development

For development setup you can set environment variables `ENV=dev`. This way default values will be used. NOT TO BE USED IN PRODUCTION!

### Testing

Run tests by executing:

```bash
make install-dev
make test
```

## License

Code released under the [GNU Affero General Public License v3.0](LICENSE).
