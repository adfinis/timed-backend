# v2.0.0

### Breaking
* **tracking:** rename field type to absence_type ([`8ca44d2`](https://github.com/adfinis/timed-backend/commit/8ca44d2f361228e7f71e3e28a795079a2e3e7745))

# v1.6.3

### Fix

* **workreport:** Update metadata ([`257e2ae`](https://github.com/adfinis/timed-backend/pull/855/commits/257e2aeedd36a112018bdedaf32191eaf0100420))
* **deps:** Bump django from 3.1.14 to 3.2.13 ([`ca8b76d`](https://github.com/adfinis/timed-backend/pull/856/commits/ca8b76dd2d1f2ce365595101bb4a6d53aa85994d))

# v1.6.2

### Fix

* **tracking:** Allow updating of billed reports ([`e73e716`](https://github.com/adfinis/timed-backend/pull/851/commits/e73e7161d51b93b14faa0a5f5babf740166aff06))

# v1.6.1

### Fix

* **projects:** Change permissions and visibility for billing types ([`8a705db`](https://github.com/adfinis/timed-backend/pull/847/commits/8a705dbca7a66abd443f0a99341004c3515f3dbd))
* **subscription:** Fix parser and notifications for orders ([`0deaafa`](https://github.com/adfinis/timed-backend/pull/849/commits/0deaafa71d8520c7bf17fc91aa938f0106f96150))

# v1.6.0

### Feature
* **env:** Add tls option for emails to env var ([`c68107a`](https://github.com/adfinis/timed-backend/pull/845/commits/c68107a4a58f54fbaa2c1de2f158437ad78609f3))

### Fix
* **reports:** Add reviewer hierarchy in `notify_reviewers_unverified` ([`91751e9`](https://github.com/adfinis/timed-backend/pull/843/commits/91751e9497ac67ecb3072e33a6c990169d8488ee))
* **subscription:** Include cost center in `SubscriptionProjectSerializer` ([`11640f8`](https://github.com/adfinis/timed-backend/pull/846/commits/11640f88d797480a5f110fc7fc9b27d262f22bfa))

# v1.5.5

### Fix
* **reports:** Center total hours column in workreport ([`1acd374`](https://github.com/adfinis/timed-backend/pull/840/commits/1acd3742af972e17d8600b560f16f7afe9a70d1d))

# v1.5.4

### Fix
* **auth:** Username should be case insensitive ([`1ce24bd`](https://github.com/adfinis/timed-backend/commit/1ce24bd04f4b217e560707bd699bbeb6fe14fe09))

# v1.5.2

### Fix
* **subscription/notify_admin:** Prevent invalid addition of datetime and int ([`645881d`](https://github.com/adfinis/timed-backend/pull/829/commits/645881d22aa7987614a13e7ee62a8f201b60c717))

# v1.5.1

### Fix
* **subscription/notify_admin:** Check project.estimate before calcualting total_hours ([`63273d2`](https://github.com/adfinis/timed-backend/commit/63273d27e9c57714ba9c01c9870a6949cfd33e91))
* **subscriptions/notify_admin:** Use dateutils parser to prevent an error ([`c3a8c6c`](https://github.com/adfinis/timed-backend/commit/c3a8c6ceb708efd309f79c6f9808231e2169dea4))

# v1.5.0

### Feat

* **settings**: add CORS_ALLOWED_ORIGINS to env (9e32bdc58171cbbd24304fb2c30d745d9e2cbe23)

# v1.4.5

### Features

* Add new `is_customer` assignee role and update permissions #810 
* Update fixtures and keycloak config #813 
* **authentication:** Update django user data according to OIDC userinfo #814 
* **subscription:** Send email on order creation #811 

### Fixes

* Fix visibility in various models to not depend on employment #808 
* **subscription:** fix visibility of subscription projects #812

# v1.4.4

### Features

* **reports:** Change column for total hours for tasks #800 
* **fixtures:** Add accountant user to fixtures #802 
* **tracking:** Add user to Report Intersection #803 
* **settings:** Make DATA_UPLOAD_MAX_NUMBER_FIELDS alterable #805 

### Fixes

* Fix setting correct value for billed flag on projects #799 
* **tracking:** Remove billed check from "editable" filter #804 
* **tracking:** Fix reviewer filter to only show reports in which the user is sole reviewer #807

# v1.4.3

### Features

* Use whitenoise to host static files #790 
* Add SECURE_PROXY_SSL_HEADER #785 

### Fixes

* Rename IsNotBilledAndVerified permission #796 
* **reports:** Add missing logo and update font in workreport #794 
* **redmine:** Fix total hours calculation #793

# v1.4.2

### Features

* Add accountant flag for users #782
* Add number filter for assignees #780 

### Fixes

* Fix calculations in workreport #781

# v1.4.1

### Fixes

Add manager role to project assignees #779 

# v1.4.0

### Features
- Serve static files for Django Admin #777 

### Fixes
- Update fixtures according to new roles #778

 
# v1.3.0 (12 August 2021)

### Feature
* Use assignees with reviewer role instead of reviewers ([`89def71`](https://github.com/adfinis/timed-backend/commit/89def71eefc0f18e7989b34f882acd2fd619998d))
* Rewrite permissions and visibilty to use with assignees and external employees ([`159e750`](https://github.com/adfinis/timed-backend/commit/159e75033ed4c477d56f2a2817dee82b3066d2a9))
* Add user assignement to customers, projects and tasks ([`6ff4259`](https://github.com/adfinis/timed-backend/commit/6ff425941307a0386d835187eaad02e26cc718e3))
* Add and enable sentry-sdk for error reporting ([`1e96b78`](https://github.com/adfinis/timed-backend/commit/1e96b785206ddd1a871e5b23a9126f50c94c38dc))
* **employment:** Add new attribute is_external to employment model ([`e8e6291`](https://github.com/adfinis/timed-backend/commit/e8e629193b7aabd592fc9744bc7210577d58c910))
* **runtime:** Use gunicorn instead of uwsgi ([`e6b1fdf`](https://github.com/adfinis/timed-backend/commit/e6b1fdfc5bb2ad5578ed2927ee210b5da2119f9b))
* **redmine:** Update template formatting ([`9b1a6f1`](https://github.com/adfinis/timed-backend/commit/9b1a6f164f72c2eae57a1e20cc0cff763c7e535a))

### Fix
* Update workreport template ([`b877194`](https://github.com/adfinis/timed-backend/commit/b87719485affd6421734251c270d1fbeb37a7176))


# v1.2.0 (16 April 2021)

### Feature
* Export metrics with django-prometheus ([`6ed9cab`](https://github.com/adfinis/timed-backend/commit/6ed9cabeeefd2e6945a63b83de1ee85018fb56a5))
* Show not_billable and review attributes for reports in weekly report ([`a02aca4`](https://github.com/adfinis/timed-backend/commit/a02aca48ae609f9ac514238be723c056fa60754f))
* Add customer_visible field to project serializer ([`2f12f86`](https://github.com/adfinis/timed-backend/commit/2f12f86d6132c1362d7065ad0fd8cf89a4f4f377))
* Add billed flag to project and tracking ([`fe41199`](https://github.com/adfinis/timed-backend/commit/fe41199527e5ab37f23c715d844805b7d8944d64))
* **projects:** Add currency fields to task and project ([`7266c34`](https://github.com/adfinis/timed-backend/commit/7266c346236e9e0d1c83d9f84b99a4e782256ba4))

### Fix
* Translate work report to English ([`7a87d93`](https://github.com/adfinis/timed-backend/commit/7a87d935893dbc68fd59a4fb477691ad209b6a3b))
* Add custom forms for supervisor and supervisee inlines ([`b92799d`](https://github.com/adfinis/timed-backend/commit/b92799d66759479827cf11f958c12d55d9c8d5bd))
* Add billable column and calculate not billable time ([`4184b76`](https://github.com/adfinis/timed-backend/commit/4184b76c66b5233d7a568cc6e37d9112ae9d939f))
* **tracking:** Set billed from project on report ([`d25e64f`](https://github.com/adfinis/timed-backend/commit/d25e64fd4c898757acb565996173f460f636c6a6))
* **tracking:** Update billed if not sent with request ([`62295ba`](https://github.com/adfinis/timed-backend/commit/62295bac19f302fa45281a72edb09397e3cbc4c6))
* Add test data users to keycloak config ([`082ef6e`](https://github.com/adfinis/timed-backend/commit/082ef6e14a406a5d3b1a5f286007169689c0cb1b))

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
