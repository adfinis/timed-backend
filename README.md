# Timed Backend
[![Build Status](https://img.shields.io/travis/adfinis-sygroup/timed-backend.svg?style=flat-square)](https://travis-ci.org/adfinis-sygroup/timed-backend)
[![Coverage](https://img.shields.io/coveralls/adfinis-sygroup/timed-backend.svg?style=flat-square)](https://coveralls.io/github/adfinis-sygroup/timed-backend)
[![License](https://img.shields.io/github/license/adfinis-sygroup/timed-frontend.svg?style=flat-square)](LICENSE)

Timed timetracking software REST API built with Django

## Installation
**Requirements**
* python 3.5.2
* docker
* docker-compose

After installing and configuring those requirements, you should be able to run the following
commands to complete the installation:
```bash
$ echo "ENV=dev" >> .env                       # Django settings will be configured for development
$ make install                                 # Install Python requirements
$ docker-compose up -d                         # Start the containers
$ make setup-ldap                              # Configure UCS LDAP container
$ make create-ldap-user                        # Create a new standard user
$ ./manage.py migrate                          # Run Django migrations
$ ./manage.py createsuperuser                  # Create a new Django superuser
```

You can now access the API at http://localhost:8000/api/v1 and the admin interface at http://localhost:8000/admin/

## Configuration

Following options can be set as environment variables to configure Timed backend in documented [format](https://github.com/joke2k/django-environ#supported-types)
according to type.

| Parameter                           | Description                                                | Default                          |
| ----------------------------------- | ---------------------------------------------------------- | -------------------------------- |
| `DJANGO_DEBUG`                      | Boolean that turns on/off debug mode                       | False                            |
| `DJANGO_SECRET_KEY`                 | Secret key for cryptographic signing                       | not set (required)               |
| `DJANGO_ALLOWED_HOSTS`              | List of hosts representing the host/domain names           | not set (required)               |
| `DJANGO_HOST_PROTOCOL`              | Protocol host is running on (http or https)                | http                             |
| `DJANGO_HOST_DOMAIN`                | Main host name server is reachable on                      | not set (required)               |
| `DJANGO_DATABASE_NAME`              | Database name                                              | timed                            |
| `DJANGO_DATABASE_USER`              | Database username                                          | timed                            |
| `DJANGO_DATABASE_HOST`              | Database hostname                                          | localhost                        |
| `DJANGO_DATABASE_PORT`              | Database port                                              | 5432                             |
| `DJANGO_AUTH_LDAP_ENABLED`          | Enable LDAP authentication                                 | False                            |
| `DJANGO_AUTH_LDAP_SERVER_URI`       | uri of LDAP server                                         | not set                          |
| `DJANGO_AUTH_LDAP_BIND_DN`          | distinguished name to use when binding to LDAP server      | not set                          |
| `DJANGO_AUTH_LDAP_PASSWORD`         | password to use with DJANGO_AUTH_LDAP_BIND_DN              | not set                          |
| `DJANGO_AUTH_LDAP_USER_DN_TEMPLATE` | template to distinguish user’s username                    | not set                          |
| `EMAIL_URL`                         | Uri of email server                                        | smtp://localhost:25              |
| `DJANGO_DEFAULT_FROM_EMAIL`         | Default email address to use for various responses         | webmaster@localhost              |
| `DJANGO_SERVER_EMAIL`               | Email address error messages are sent from                 | root@localhost                   |
| `DJANGO_ADMINS`                     | List of people who get error notifications                 | not set                          |
| `DJANGO_WORK_REPORT_PATH`           | Path of custom work report template                        | not set                          |


## Testing
Run tests by executing `make test`

## License
Code released under the [GNU Affero General Public License v3.0](LICENSE).
