# v1.1.3 (26 April 2021)

### Feature

* Export metrics with django-prometheus ([`6ed9cab`](https://github.com/adfinis-sygroup/timed-backend/commit/6ed9cabeeefd2e6945a63b83de1ee85018fb56a5))
* Add customer_visible field to project serializer ([`2f12f86`](https://github.com/adfinis-sygroup/timed-backend/commit/2f12f86d6132c1362d7065ad0fd8cf89a4f4f377))

### Fix
* Add custom forms for supervisor and supervisee inlines ([`b92799d`](https://github.com/adfinis-sygroup/timed-backend/commit/b92799d66759479827cf11f958c12d55d9c8d5bd))
* Add test data users to keycloak config ([`082ef6e`](https://github.com/adfinis-sygroup/timed-backend/commit/082ef6e14a406a5d3b1a5f286007169689c0cb1b))

# v1.1.2 (28 October 2020)

### Fix
* fix user based permissions to use the IS_AUTHENTICATED permission properly (#654)


# v1.1.1 (14 August 2020)

### Fix
* increase uwsgi buffer-size for big query strings


# v1.1.0 (11 August 2020)

### Feature
* implement SSO OIDC login for django admin
* django-local user/password (django-admin) login is now a toggable setting, see `DJANGO_ALLOW_LOCAL_LOGIN`


# v1.0.0 (30 July 2020)

See Github releases for changelog of previous versions.
