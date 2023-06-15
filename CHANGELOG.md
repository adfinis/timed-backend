# v3.0.7

### Fix
* **redmine:** Convert Decimal objects to floats ([`5f613d1`](https://github.com/adfinis/timed-backend/commit/5f613d1e83f007270228c109846fb6a525eced71))

# v3.0.6

### Feature
* **redmine:** Add redmine issue id to log ([`b5c509b`](https://github.com/adfinis/timed-backend/commit/b5c509bc196137b28e84b814d4dba0a60b117747))

# v3.0.5

### Fix
* **tracking:** Fix updating own rejected reports and rejecting own reports ([`6a5d0ed`](https://github.com/adfinis/timed-backend/commit/6a5d0eda470939c59ad9ea869d4296e0115dd33e))

# v3.0.4

### Fix
* **redmine:** Log estimated_hours in update_project_expenditure command ([`fc1f631`](https://github.com/adfinis/timed-backend/commit/fc1f631a7fcdc25ab93b5cbcf38845f30af3f4a5))

# v3.0.3

### Fix
* **redmine:** Fix value check for custom fields ([`5f6bc53`](https://github.com/adfinis/timed-backend/commit/5f6bc532c6e0d76c9dae07b423afa6ea7c2ab52c))

# v3.0.2

### Fix
* **redmine:** Fix NoneType for amount offered/invoiced for projects ([`6e1f4c8`](https://github.com/adfinis/timed-backend/commit/6e1f4c89672a991ce1765bbed7c5e71f02a119e2))

# v3.0.1

### Feature
* Empty sums in correcr ordering ([`757de4e`](https://github.com/adfinis/timed-backend/commit/757de4e263cd42bb8521bccdd51dc6bf2207e761))
* **statistics:** Support ordering in new queryset wrapper ([`fb5a2dc`](https://github.com/adfinis/timed-backend/commit/fb5a2dc6480936004d90c067161905196aad58e0))

### Fix
* **tracking:** Fix report update notifactions ([`8d0d0fd`](https://github.com/adfinis/timed-backend/commit/8d0d0fd62896652a15ed00b840090cccdc4eaac8))
* **tests:** Customer statistic test had a missing customer ([`c99b512`](https://github.com/adfinis/timed-backend/commit/c99b5120fce4f3dc8bddf21346eb46bb8ba72239))
* **pytest:** Ignore "invalid escape sequence" deprecation warning ([`4e08672`](https://github.com/adfinis/timed-backend/commit/4e086727a1e69e658e5c044930ce1248aa9c1435))
* **statistics:** Refactor multiqs to use filtering aggregates ([`345b8df`](https://github.com/adfinis/timed-backend/commit/345b8df559593b03f69dcc1b81c590a4277d8fda))
* **makefile:** Use aliases for debug backend ([`9c47123`](https://github.com/adfinis/timed-backend/commit/9c47123af4cab3ab2095b9ff1b0e63ca973ee6ac))

# v3.0.0

### Feature
* **filters:** Add number multi value filter ([`4688e41`](https://github.com/adfinis/timed-backend/commit/4688e41da5300d789ed50bdd6af34d7d481767c8))
* **redmine:** Add pretend mode to redmine commands ([`abc5083`](https://github.com/adfinis/timed-backend/commit/abc50834feb3f84d3018abaa31073ab68e79dd76))
* **notifications:** Project budget check notifications ([`b81e28e`](https://github.com/adfinis/timed-backend/commit/b81e28e9d0b8386e54caf57b90960e392d5811c0))
* **statistics:** Show amount offered and invoiced in project statistics ([`144444b`](https://github.com/adfinis/timed-backend/commit/144444b298f2139f44a8ca291ca34ccfb3f66899))
* **redmine:** Import project expenditure from redmine ([`766f79b`](https://github.com/adfinis/timed-backend/commit/766f79bc17ce927a05217e9bacc18c478404e6f6))
* **redmine:** Update expenditures on redmine projects ([`0aa9da6`](https://github.com/adfinis/timed-backend/commit/0aa9da69e8432a4d9537b65dd935bebe23fd4c72))
* **filters:** Allow filtering of tasks and reports in statistics ([`b5b9c8d`](https://github.com/adfinis/timed-backend/commit/b5b9c8d633a4d6fc8633594349feec7ee59fb8d0))
* **employment:** Add is_external filter for user endpoint ([`8a1b272`](https://github.com/adfinis/timed-backend/commit/8a1b2723147c9775cb06abd090ec307610a2d254))
* **admin:** Add searchable dropdowns for user lists in admin ([`4c01054`](https://github.com/adfinis/timed-backend/commit/4c010542ce3b3544c3e87f1dd2ca7ff8ec4df245))
* Track remaining effort on tasks ([`3d045f2`](https://github.com/adfinis/timed-backend/commit/3d045f21ed7fd2147b49c6190dc3e1474c69decb))
* **tracking:** Reject reports ([`a4e8983`](https://github.com/adfinis/timed-backend/commit/a4e8983265d0b87101a6151982fbb8a802e4cd9a))

### Fix
* **tracking:** Fix automatic unreject when bulk updating ([`f110eb0`](https://github.com/adfinis/timed-backend/commit/f110eb0ea864a7115f7ed1d24e868aafb6c038f2))
* **tracking:** Fix remaining effort on report creation ([`abceb32`](https://github.com/adfinis/timed-backend/commit/abceb322e042df5c34b04e685c331527848c898f))
* **tracking:** Fix setting of remaining effort ([`16f1dbb`](https://github.com/adfinis/timed-backend/commit/16f1dbb54f625a8468fd33066a685ac1cfae7fec))
* **notifications:** Omit projects with no reports ([`91a6dd5`](https://github.com/adfinis/timed-backend/commit/91a6dd5ec2d128d6df3994c78eebbb295ec9a2f5))
* **tracking:** Allow null values on remaining effort for reports ([`08a5aa4`](https://github.com/adfinis/timed-backend/commit/08a5aa429eac6d25cec0699a42919ee8f959ed12))
* **tracking:** Fix  absence for users with multiple employments ([`d884ef6`](https://github.com/adfinis/timed-backend/commit/d884ef6a4463e5095fcecc6cd999aa6b595f5530))
* Add missing rejected field to ReportIntersectionSerializer ([`ee8f79a`](https://github.com/adfinis/timed-backend/commit/ee8f79a1a724763bdd51222010f47ec40ef71622))
* **auth:** Let failing auth requests return 401 ([`8454601`](https://github.com/adfinis/timed-backend/commit/8454601019f33272a39814ac8e3fe033c758e7e7))
* **dev:** Remove deprecated flag from pre-commit isort ([`50e5da2`](https://github.com/adfinis/timed-backend/commit/50e5da2ad5ef12098e0128ba907ac40ac2fa1773))
* **tracking:** Fix remaining effort check when creating report ([`fc7c92c`](https://github.com/adfinis/timed-backend/commit/fc7c92cf0f3cb937100616abb24bd06804408a51))
* **statistics:** Add missing fields for project and task statistics ([`89fb718`](https://github.com/adfinis/timed-backend/commit/89fb718901f41914323a60d99a2983ba0454daa0))
* **reports:** Fix project and customer statistics ([`a3ab8ac`](https://github.com/adfinis/timed-backend/commit/a3ab8acb5be4107ea7f4f6677cdbdb57dd0b95c2))
* **projects:** Ignore signal when loading a fixture ([`21e5dd7`](https://github.com/adfinis/timed-backend/commit/21e5dd7861a52793cf4b40e94c04de78a64ca3ec))
* **container:** Executable bit for cmd.sh ([`34f2751`](https://github.com/adfinis/timed-backend/commit/34f27517c896577ddca3e1355cdc3ba5b8233d29))
* **filters:** Allow Q filtering for MultiQS querysets ([`b629c9d`](https://github.com/adfinis/timed-backend/commit/b629c9d97cec7d4779baaa94f6eb628b394a3c53))
* **reports:** Refactor statistics ([`21d3677`](https://github.com/adfinis/timed-backend/commit/21d36774816467977f6a45bab0641d7abf4d6ec5))


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
