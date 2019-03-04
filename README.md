# SciPost
This repository carries the entire codebase for the [scipost.org](https://scipost.org) scientific publication portal.

## Project organization
Development work for SciPost is headed by [Jean-Sébastien Caux](https://jscaux.org) and Jorran de Wit. Bug reports, issues, suggestions and ideas can be emailed to [techsupport@scipost.org](mailto:techsupport@scipost.org).

If you are competent in web development and would like to join our core development team, please email your credentials to [jscaux@scipost.org](mailto:jscaux@scipost.org).

## License
This codebase is released under the terms of the GNU Affero General Public License (Version 3, 19 November 2007).

## Dependencies
SciPost is written in Python 3.5 using Django 1.11 and requires PostgreSQL 9.4 or
higher. Python dependencies are listed in `requirements.txt`. Frontend dependencies are managed by [NPM](https://www.npmjs.com/) in package.json.

## Getting started

### Database
Make sure that PostgreSQL is installed and running and that a database with user is set up. A
good guide how to do this can be found [here](https://djangogirls.gitbooks.io/django-girls-tutorial-extensions/content/optional_postgresql_installation/) (NOTE: stop before the 'Update settings' part).

### Python version
Make sure you're using Python 3.5. You are strongly encouraged to use a [virtual environment](https://docs.python.org/3.5/library/venv.html).


```shell
$ pyvenv scipostenv
$ source scipostenv/bin/activate
```

Now install dependencies:

```shell
(scipostenv) $ pip install -r requirements.txt
```

### Frontend dependencies
[NPM](https://www.npmjs.com/) (version 5.x; tested on v5.3.0) will take care of frontend dependencies. To install all packages now run:

```shell
(scipostenv) $ npm install
```

### Settings
In this project, many settings are not sensitive and are thus tracked using Git. Some settings are however secret. These settings may be saved into the  `secrets.json` file in the root of the project. The minimum required structure is as follows (please mind the non-empty, but still invalid `SECRET_KEY`):

```json
{
  "SECRET_KEY": "<key>",
  "DB_NAME": "",
  "DB_USER": "",
  "DB_PWD": ""
}
```

The settings file itself is saved into `SciPost_v1/settings/local_<name>.py`. Be sure to *wildcard import* the `base.py` file in the top of your settings file. To run the server, use one of two ways. Either:

```shell
(scipostenv) $ ./manage.py runserver --settings=SciPost_v1.settings.local_<name>
```

... or for convenience, export the same settingsfile path to the `DJANGO_SETTINGS_MODULE` variable, so that one can run the django commands by default:

```shell
(scipostenv) $ export DJANGO_SETTINGS_MODULE="SciPost_v1.settings.local_<name>"
```

One can of course also add this variable to the `~/.bash_profile` for convenience.

### Mail

In the `mails` application a special [Email Backend](https://docs.djangoproject.com/en/1.11/topics/email/#email-backends) is defined. This will write all emails to the database. To use this backend, in the settings set the the variable `EMAIL_BACKEND` as:

```python
# settings.py
EMAIL_BACKEND = 'mails.backends.filebased.ModelEmailBackend'
EMAIL_BACKEND_ORIGINAL = 'mails.backends.filebased.EmailBackend'
```

A management command is defined to send the unsent mails in the database. This management command uses the Email Backend defined in the settings under variable `EMAIL_BACKEND_ORIGINAL`. If not defined, this defaults to the Django default: `django.core.mail.backends.smtp.EmailBackend`.

```shell
(scipostenv) $ ./manage.py send_mails
```

### Check, double check
To make sure everything is set up and correctly configured, run:

```shell
(scipostenv) $ ./manage.py check
```

### Module bundler
[Webpack](https://webpack.js.org/) takes care of assets in the `scipost/static/scipost/assets` folder. To (re)compile all assets into the `static_bundles` folder, simply run:

```shell
(scipostenv) $ npm run webpack
```

While editing assets, it may be helpful to put Webpack in _watch_ mode. This will recompile your assets in real time. To do so, instead of the above command, run:

```shell
(scipostenv) $ npm run webpack-live
```

#### Sass and Bootstrap
Styling will mainly be configured using [.scss files](http://www.sass-lang.com/) in the `scipost/static/scipost/scss/preconfig.scss` file, relying on [Bootstrap v4.0.0-beta](//www.getbootstrap.com/). A full list of variables available by default can be found [here](https://github.com/twbs/bootstrap/blob/v4-dev/scss/_variables.scss).
All modules are configured in the `.bootstraprc` file. All modules are disabled by default.

### Collectstatic
In order to collect static files from all `INSTALLED_APPS` (i.e. the assets managed by Webpack), run:

```shell
(scipostenv) $ ./manage.py collectstatic
```

This will put all static files in the `STATIC_ROOT` folder defined in your settings file. If needed, you can remove stale static files through:

```shell
(scipostenv) $ ./manage.py collectstatic --clear
```

### Create and run migrations
Now that everything is set up, we can create the relevant tables in the database:
```shell
(scipostenv) $ ./manage.py migrate
```

### Create a superuser
In order to use the admin site, you'll need a superuser account, which can be created using:
```shell
(scipostenv) $ ./manage.py createsuperuser
```

### Create groups and permissions
Groups and their respective permissions are set using the management command:

```shell
(scipostenv) $ ./manage.py add_groups_and_permissions
```

### Run server
You are now ready to run the server:

```shell
(scipostenv) $ ./manage.py runserver
```

## Contributors
Users of the SciPost portal are known as Contributors and are created through the registration form accessible from the home page.

You can create a number of users, and use the admin site to give them various permissions through memberships of certain groups. For example, you'll want members of the SciPost Administrators and Editorial Administrators groups in order to access the internal management and editorial tools.

## Initial data
If you're working on an (almost) empty test database, you can easily fill it using one of the built-in commands. To create a few instances for each available object, simply run:

```shell
(scipostenv) $ ./manage.py populate_db --all
```

Run the same command with the `--help` argument to find arguments to create instances for individual models:

```shell
(scipostenv) $ ./manage.py populate_db --help
```


## Maintaining database migrations
Every time fields in any of the models change, a [database migration](https://docs.djangoproject.com/en/1.11/topics/migrations/)
needs to be created and applied. The first documents a database change and its
inverse, the second actually changes the database.

Make sure to commit the migration to Git after applying it, so other developers
can use them.

```shell
(scipostenv) $ ./manage.py makemigrations
(scipostenv) $ ./manage.py migrate
```

## Search engine
[Django Haystack]() is used to handle search queries. The search engine needs indexing before you can use it:

```shell
(scipostenv) $ ./manage.py update_index -u default
```
Models involved in searches are re-indexed using `post_save` signals.

## Scheduled tasks
The tasks that involve large requests from CR are supposed to run in the background. For this to work, Celery is required. The following commands assume that you are in the `scipost_v1` main folder, inside the right virtual environment.

Celery depends on a broker, for which we use RabbitMQ. Start it with
```bash
nohup rabbitmq-server > ../logs/rabbitmq.log 2>&1 &
```

Then the Celery worker itself:
```bash
nohup celery -A SciPost_v1 worker --loglevel=info -E > ../logs/celery_worker.log 2>&1 &
```

And finally `beat`, which enables setting up periodic tasks:
```bash
nohup celery -A SciPost_v1 beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler > ../logs/celery_beat.log 2>&1 &
```

## Documentation
All project documentation is gathered from `.rst` files and code-embedded docstrings.
The documentation for the codebase can be found in `docs/codebase`.

### Sphinxdoc
The documentation is saved in the local database as a Project with name `SciPost Codebase`,
with slug `codebase` and path `/docs/codebase`
(this project should be manually created in the admin under the `Sphinxdoc` app).

To update the docs, simply run
```shell
(scipostenv) $ ./manage.py updatedoc -b codebase
```

The documentation is then viewable by navigating to `docs/codebase`.

There are also other Projects containing information about SciPost, user guides etc. The list can be found on by viewing `docs` in the browser.


### Locally-served documentation
The documentation can be rendered using
[Sphinx](http://www.sphinx-doc.org/). Note that rendering documentation is only
available from the virtual environment - and only when the host settings have
been configured.

To build the documentation, run:

```shell
(scipostenv) $ cd docs/[project slug]
(scipostenv) $ make html
```

for each of the documentation projects.
After this, generated documentation are available in `docs/[project slug]/_build/html`.

## Templated emails
The `mails` app is used as the (templated) mailing processor of SciPost. Each email is defined using two files: the template and the configuration file.

Each mail is defined using certain general configuration possibilities. These options are defined in the json configuration file or are overwritten in the methods described below. These fields are:

* `subject` {string}
> The subject of the mail.

* `recipient_list` and `bcc` {list}
> Both fields are lists of strings. Each string may be either a plain mail address, eg. ` example@scipost.org`, or it may represent a certain relation to the central object. For example, one may define:
```python
>>> sub_1 = Submission.objects.first()
>>> mail_util = DirectMailUtil([...], object=sub_1, recipient_list=['example@scipost.org', 'submitted_by.user.email'])
```

* `from_email` {string}
> For this field, the same flexibility and functionality exists as for the `recipient_list` and `bcc` fields. However, this field should always be a single string entry.
```python
>>> mail_util = DirectMailUtil([...], from_email='noreply@scipost.org')
```

* `from_name` {string}
> The representation of the mail sender.

### Central object
#### Using a single Model instance
The "central object" is a *django.db.models*.__Model__ instance that will be used for the email fields if needed and in the template. The mail engine will try to automatically detect a possible Model instance and save this in the template context as `<Model.verbose_name>` and `object`. The keyword you use to send it to the mail engine is not relevant for this method, but will be copied to be used in the template as well.

##### Example
```python
>>> sub_1 = Submission.object.first()
>>> mail_util = DirectMailUtil([...], weird_keyword=sub_1)
```

Now, in the template, the variables `weird_keyword`, `submission` and `object` will all represent the `sub_1` instance. For example:

```html
<h1>Dear {{ weird_keyword.submitted_by.get_title_display }} {{ object.submitted_by.user.last_name }},</h1>
<p>Thank you for your submission: {{ submission.title }}.</p>
```

#### Using multiple Model instances
If a certain mail requires more than one Model instance, it is required to pass either a `instance` or `object` parameter for the mail engine to determine the central object.

##### Example
```python
>>> sub_1 = Submission.object.first()
>>> report_1 = Report.object.first()
>>> mail_util = DirectMailUtil([...], submission=sub_1, report=report_1)
ValueError: "Multiple db instances are given."
```

Here, it is required to pass either the `instance` or `object` parameter, eg.:
```python
>>> mail_util = DirectMailUtil([...], object=sub_1, report=report_1)
```

#### Configuration file

File: *templates/email/*__<mail_code>.json__

Each mail is configured with a json file, which at least contains a `subject` and `recipient_list` value. The other fields are optional. An example of all available configuration fields are shown:
```json
{
    "subject": "Foo subject",
    "recipient_list": [
        "noreply@scipost.org"
    ],
    "bcc": [
        "secret@scipost.org"
    ],
    "from_email": "server@scipost.org",
    "from_name": "SciPost Techsupport"
}
```

#### Template file

File: *templates/email/*__<mail_code>.html__

Any mail will be defined in the html file using the conventions as per [Django's default template processor](https://docs.djangoproject.com/en/1.11/topics/templates/).

### Direct mail utility
The fastest, easiest way to use templated emails is using the `DirectMailUtil` class.

*class* mails.utils.__DirectMailUtil(__*mail_code, delayed_processing=True, subject='', recipient_list=[], bcc=[], from_email='', from_name='', \**template_variables*__)__

##### Attributes
* `mail_code` {string}
> The unique code refereeing to a template and configuration file.

* `delayed_processing` {boolean, optional}
> Execute template rendering in a cronjob to reduce executing time.

* `subject` {string, optional}
> Overwrite the `subject` field defined in the configuration field.

* `recipient_list` {list, optional}
> Overwrite the `recipient_list` field defined in the configuration field.

* `bcc` {list, optional}
> Overwrite the `bcc` field defined in the configuration field.

* `from_email` {string, optional}
> Overwrite the `from_email` field defined in the configuration field.

* `from_name` {string, optional}
> Overwrite the `from_name` field defined in the configuration field.

* `**template_variables`
> Append any keyword argument that may be used in the email template.

##### Methods

* `send_mail()`
> Send the mail as defined on initialization.

##### Basic example
```python
>>> from mails.utils import DirectMailUtil
>>> mail_util = DirectMailUtil('test_mail_code_1')
>>> mail_util.send_mail()
```
This utility is protected to prevent double sending. So now, the following has no effect anymore:
```python
>>> mail_util.send_mail()
```


### Class-based view editor
 This acts like a regular Django class-based view, but will intercept the post request to load the email form and submit when positively validated.

This view may be used as a [generic editing view](https://docs.djangoproject.com/en/1.11/ref/class-based-views/generic-editing/) or [DetailView](https://docs.djangoproject.com/en/1.11/ref/class-based-views/generic-display/#detailview).


*class* mails.views.__MailView__

This view is a basic class-based view, which may be used as basic editor for a specific templated email.

##### Attributes
* `mail_code` {string}
> The unique code refereeing to a template and configuration file.

* `mail_config` {dict, optional}
> Overwrite any of the configuration fields of the configuration file:
    * `subject` {string}
    * `recipient_list` {list}
    * `bcc` {list}
    * `from_email` {string}
    * `from_name` {string}

* `mail_variables` {dict, optional}
> Append extra variables to the mail template.

* `fail_silently` {boolean, optional}
> If set to False, raise PermissionDenied is `can_send_mail()` returns False on POST request.

##### Methods
* `can_send_mail()`
> Control permission to actually send the mail. Return a __boolean__, returns `True` by default.

* `get_mail_config()`
> Return an optional explicit mail configuration. Return a __dictionary__, returns `mail_config` by default.


*class* mails.views.__MailFormView__

This view may be used as a generic editing view, and will intercept the POST request to let the user edit the email before saving the original form and sending the templated mail.

##### Attributes
* `form_class` {django.forms.__ModelForm__ | django.forms.__Form__}
> The original form to use as in any regular Django editing view.

* `mail_code` {string}
> The unique code refereeing to a template and configuration file.

* `mail_config` {dict, optional}
> Overwrite any of the configuration fields of the configuration file:
    * `subject` {string}
    * `recipient_list` {list}
    * `bcc` {list}
    * `from_email` {string}
    * `from_name` {string}

* `mail_variables` {dict, optional}
> Append extra variables to the mail template.

* `fail_silently` {boolean, optional}
> If set to False, raise PermissionDenied is `can_send_mail()` returns False on POST request.

##### Methods
* `can_send_mail()`
> Control permission to actually send the mail. Return a __boolean__, returns `True` by default.

* `get_mail_config()`
> Return an optional explicit mail configuration. Return a __dictionary__, returns `mail_config` by default.


##### Basic example
```python
# <app>/views.py
from mails.views import MailView

class FooView(MailView):
    mail_code = 'test_mail_code_1'
```
```python
# <app>/urls.py
from django.conf.urls import url

from .views import FooView

urlpatterns = [
    url(r'^$', FooView.as_view(), name='foo'),
]
```

### Function-based view editor
Similar as to the `MailView` it is possible to have the user edit a templated email before sending in function-based views, using the `MailEditorSubview`.

*class* mails.views.__MailEditorSubview(__*request, mail_code, header_template='', context={}, subject='', recipient_list=[], bcc=[], from_email='', from_name='', \**template_variables*__)__

##### Attributes
* `request` {django.http.__HttpResponse__}
> The HttpResponse which is typically the first parameter in a function-based view.

* `mail_code` {string}
> The unique code refereeing to a template and configuration file.

* `header_template` {string, optional}
> Any template that may be used in the header of the edit form.

* `context` {dict, optional}
> A context dictionary as in any usual Django view, which may be useful combined with `header_template`.

* `subject` {string, optional}
> Overwrite the `subject` field defined in the configuration field.

* `recipient_list` {list, optional}
> Overwrite the `recipient_list` field defined in the configuration field.

* `bcc` {list, optional}
> Overwrite the `bcc` field defined in the configuration field.

* `from_email` {string, optional}
> Overwrite the `from_email` field defined in the configuration field.

* `from_name` {string, optional}
> Overwrite the `from_name` field defined in the configuration field.

* `**template_variables`
> Append any keyword argument that may be used in the email template.

##### Methods
* `is_valid()`
> See if data is returned and valid, similar to Django forms. Returns a __boolean__.

* `interrupt()`
> Interrupt request by rendering the templated email form. Returns a [__HttpResponse__](https://docs.djangoproject.com/en/2.1/ref/request-response/#django.http.HttpResponse).

* `send_mail()`
> Send email as edited by the user in the template.


##### Basic example
```python
from submissions.models import Submission
from mails.views import MailEditorSubview

def any_method_based_view(request):
    submission = Submission.objects.first()
    mail_request = MailEditorSubview(request, 'test_mail_code_1', object=submission)
    if mail_request.is_valid():
        mail_request.send_mail()
        return redirect('reverse:url')
    else:
        return mail_request.interrupt()
```

### Important epilogue
Every templated mail defined in the `templates/email/` folder will be tested for proper configuration. This tests includes tests on the configuration file and existence of the template. Important note: it does not test the content of the templates (read: the variables used in the template). To run these, and all other mail-related unit tests, simple run the following:

```shell
(scipostenv) $ ./manage.py test mails.tests -k
```

A successful test ends by printing "OK". In any other case, errors will be raised.


## Django-extensions
[django-extensions](https://github.com/django-extensions/django-extensions) provide added commands like
`./manage.py shell_plus`, which preloads all models in a shell session. Additional imports may be specified in `settings.py` as follows:

```python
SHELL_PLUS_POST_IMPORTS = (
    ('theses.factories', ('ThesisLinkFactory')),
    ('comments.factories', ('CommentFactory')),
)
```

## Scheduled tasks
The tasks that involve large requests from CR are supposed to run in the background. For this to work, Celery is required. The following commands assume that you are in the `scipost_v1` main folder, inside the right virtual environment.

Celery depends on a broker, for which we use RabbitMQ. On MacOS one may simply install this by executing:

```shell
$ brew update
$ brew install rabbitmq
```

To start the RabbitMQ broker:
```bash
nohup nice rabbitmq-server > ../logs/rabbitmq.log 2>&1 &
```

Then the Celery worker itself:
```bash
nohup nice celery -A SciPost_v1 worker --loglevel=info -E > ../logs/celery_worker.log 2>&1 &
```

And finally `beat`, which enables setting up periodic tasks:
```bash
nohup nice celery -A SciPost_v1 beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler > ../logs/celery_beat.log 2>&1 &
```

Note: on the staging server, these commands are contained in two shell scripts in the `scipoststg` home folder. Just run
```bash
./start_celery.sh
```
