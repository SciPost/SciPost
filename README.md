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

## Mails
The `mails` app is used as the mailing processor of SciPost.
It may be used in one of two possible ways: with or without editor.

The actual mails only have to be written in the html version
(the text based alternative is automatically generated before sending).
Creating a new `mail_code` is easily done by creating new files in the `mails/templates/mail_templates` folder called `<mail_code>.html` and `<mail_code>.json` acting as resp. a content and configuration file.

##### The config file is configured as follows
`mails/templates/mail_templates/<mail_code>.json`

* `context_object` - (_required_) Instance of the main object. This instance needs to be passed as `instance` or `<context_object>` in the views and as `<context_object>` in the template file (see description below);
* `subject` - (_string, required_) Default subject value;
* `to_address` - (_string or path of properties, required_) Default to address;
* `bcc_to` - (_string or path of properties, optional_) - A comma-separated bcc list of mail addresses;
* `from_address` - (_string, optional_) - From address' default value: `no-reply@scipost.org`;
* `from_address_name` - (_string, optional_) - From address name's default value: `SciPost`.


### Mailing with editor
Any regular method or class-based view may be used together with the builtin wysiwyg editor. The class-based views inherited from Django's UpdateView are easily extended for use with the editor.

```python
from django.views.generic.edit import UpdateView
from mails.views import MailEditorMixin

class AnyUpdateView(MailEditorMixin, UpdateView):
    mail_code = '<any_valid_mail_code>'
```

For method-based views, one implements the mails construction as:

```python
from mails.views import MailEditingSubView

def any_method_based_view(request):
    # Initialize mail view
    mail_request = MailEditingSubView(request, mail_code='<any_valid_mail_code>', instance=django_model_instance)
    if mail_request.is_valid():
        # Send mail
        mail_request.send()
        return redirect('reverse:url')
    else:
        # Render the wsyiwyg editor
        return mail_request.return_render()
```

### Direct mailing
Mailing is also possible without intercepting the request for completing or editing the mail's content. For this, use the `DirectMailUtil` instead.

```python
from mails.utils import DirectMailUtil

def any_python_method_within_django():
    # Init mailer
    mail_sender = DirectMailUtil(mail_code='<any_valid_mail_code>', instance=django_model_instance)

    # Optionally(!) alter from_address from config file
    mail_sender.set_alternative_sender('SciPost Refereeing', 'refereeing@scipost.org')

    # Send the actual mail
    mail_sender.send()
    return
```

## Django-extensions
[django-extensions](https://github.com/django-extensions/django-extensions) provide added commands like
`./manage.py shell_plus`, which preloads all models in a shell session. Additional imports may be specified in `settings.py` as follows:

```python
SHELL_PLUS_POST_IMPORTS = (
    ('theses.factories', ('ThesisLinkFactory')),
    ('comments.factories', ('CommentFactory')),
)
```

## Metacore (still in development)
The Metacore app for citables, sourced - for now only - from Crossref, is available at /metacore.
In order to get it running on the server (right now implemented on staging), the following things need to be running:

First of all the Mongo daemon:
```bash
/home/scipoststg/webapps/mongo/mongodb-linux-x86_64-amazon-3.6.3/bin/mongod --auth --dbpath /home/scipoststg/webapps/mongo/data --port 21145 --logpath /home/scipoststg/webapps/scipost/logs/mongod.log --fork
```

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

Note: on the staging server, these commands are contained in two shell scripts in the `scipoststg` home folder. Just run
```bash
./start_mongod.sh
./start_celery.sh
```
