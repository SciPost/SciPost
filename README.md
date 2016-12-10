# SciPost
The complete scientific publication portal

## Dependencies
SciPost is written in Python 3.5 using Django and requires PostgreSQL 9.3 or
higher. Python dependencies are listed in `requirements.txt`.

## Getting started

### Database
Make sure that Postgres is installed and running, and that a database and user are set up for it. A
good guide how to do this can be found [here](https://djangogirls.gitbooks.io/django-girls-tutorial-extensions/content/optional_postgresql_installation/) (NOTE: stop before the 'Update settings' part).

### Python version
Make sure you're using Python 3.5. If you need to use multiple versions of Python, use [pyenv](https://github.com/yyuu/pyenv).

### Python dependencies
Setup a virtual environment using[(py)venv](https://docs.python.org/3/library/venv.html), and activate it:

```shell
$ pyvenv scipostenv
$ source scipostenv/bin/activate
```

Now install dependencies:

```shell
(scipostenv) $ pip install -r requirements.txt
```

### Host-specific settings
In this project, host-specific settings are defined in the `scipost-host-settings.json` file in the directory *above* the project root. The structure is as follows:

```json
{
    "SECRET_KEY": "<change_me>",
    "CERTFILE": "none",
    "DEBUG": true,
    "ADMINS": "",
    "ALLOWED_HOSTS": ["localhost", "127.0.0.1"],
    "SESSION_COOKIE_SECURE": false,
    "CSRF_COOKIE_SECURE": false,
    "DB_NAME": "scipost",
    "DB_USER": "scipost",
    "DB_PWD": "",
    "MEDIA_ROOT": "<media_dir>",
    "MEDIA_URL": "/media/",
    "STATIC_URL": "/static/",
    "STATIC_ROOT": "<static_dir>",
    "EMAIL_BACKEND": "django.core.mail.backends.filebased.EmailBackend",
    "EMAIL_FILE_PATH": "<email_dir>",
    "EMAIL_HOST": "",
    "EMAIL_HOST_USER": "",
    "EMAIL_HOST_PASSWORD": "",
    "DEFAULT_FROM_EMAIL": "",
    "SERVER_EMAIL": "",
    "JOURNALS_DIR": "<journals_dir>",
    "CROSSREF_LOGIN_ID": "",
    "CROSSREF_LOGIN_PASSWORD": ""
}
```

### Check, double check
To make sure everything is setup and configured well, run:

```shell
(scipostenv) $ ./manage.py check
```

### Create and run migrations
Now that everything is setup, we can setup the datastructures.
```shell
(scipostenv) $ ./manage.py migrate
```

### Create a superuser
In order to use the admin site, you'll need a superuser.
```shell
(scipostenv) $ ./manage.py createsuperuser
```

### Create groups and permissions
Groups and their respective permissions are created using the management command. Since users depend on the *Contributor* object to work properly, setup the first (admin) user using the `-u` and `-a` arguments.

```shell
(scipostenv) $ ./manage.py add_groups_and_permissions -u=<username> -a
```

### Run development server
You are now ready to run the development server:

```shell
(scipostenv) $ ./manage.py runserver
```

### Contributors
Users of the portal are known as Contributors and are created through the registration form accessible from the home page.

You can create a number of users, and use the admin site to give them various permissions through memberships of certain groups. For example, you'll want members of the SciPost Administrators and Editorial Administrators groups in order to access the internal management and editorial tools.

## Maintaining database migratons
Every time fields in any of the models change, a [database migration](https://docs.djangoproject.com/en/1.10/topics/migrations/)
needs to be created and applied. The first documents a database change and its
inverse, the second actually changes the database.

Make sure to commit the migration to GIT after applying it, so other developers
can use them.

```shell
(scipostenv) $ ./manage.py makemigration
(scipostenv) $ ./manage.py migrate
```
