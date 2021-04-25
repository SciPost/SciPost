#####################
Installing SciPost
#####################

This guide will walk you through a basic installation of the
SciPost platform.

********
Database
********

SciPost runs on the `Postgresql <https://www.postgresql.org/>`_ relational database.

Make sure that PostgreSQL 9.4 (or higher) is installed (see `instructions <https://wiki.postgresql.org/wiki/Detailed_installation_guides>`_) and running on your system.

You will need to create a database user. You can find many guides online on how to do this.

* Postgres creates a user `postgres` by default. Start a shell session for this user::

    $ sudo su - postgres

* Log into a postgres session::

    $ psql

* Create the database (let's assume from now on that you'll call your
  database `scipost_database`)::

    CREATE DATABASE scipost_database;

* Create the database user which SciPost will use to connect and interact
  with the database::

    CREATE USER scipost_db_user WITH PASSWORD [password];

* Give needed privileges to the user::

    GRANT ALL PRIVILEGES ON DATABASE scipost_database TO scipost_db_user;

* Quit postgres session::

    \q

* Go back to your regular user's shell session::

    $ exit

You will need the database username and password in your basic Django settings below.


**************
Python version
**************

Python comes in multiple versions, which in principle can lead to lots of
incompatibility problems on your system. Thankfully there exists a nifty
version management system, `pyenv <https://github.com/pyenv/pyenv>`_.
This allows you to hold multiple versions on your system, and determine
locally/globally which ones should be used.

SciPost runs on Python 3.5. You are strongly encouraged to use a
`virtual environment <https://docs.python.org/3.5/library/venv.html>`__::

   $ pyvenv scipostenv
   $ source scipostenv/bin/activate

(N.B.: this is Python 3.5-specific; for 3.6 and above, pyvenv has been deprecated
in favour of using `python -m venv [path to new venv]`).

Now install dependencies::

   (scipostenv) $ pip install -r requirements.txt


*********************
Frontend dependencies
*********************

`NPM <https://www.npmjs.com/>`__ (version 5.x; tested on v5.3.0) will
take care of frontend dependencies. To install all packages, run::

   (scipostenv) $ npm install


********
Settings
********

In this project, many settings are not sensitive and are thus tracked
using Git. Some settings are however secret. These settings may be saved
into the ``secrets.json`` file in the root of the project (you should of course
ensure that this file is excluded from the Git repository). The minimum
required structure is as follows
(you'll have to generate your own ``SECRET_KEY``; the database name,
user and password are the ones you set up in Database above; the
``CELERY_BROKER_URL`` can be left blank for now)::

     {
       "SECRET_KEY": "<key>",
       "DB_NAME": "",
       "DB_USER": "",
       "DB_PWD": "",
       "CELERY_BROKER_URL": "",
       "DISCOURSE_SSO_SECRET": ""
     }

The settings file itself is saved into
``SciPost_v1/settings/local_<name>.py``. Be sure to *wildcard import*
the ``base.py`` file at the top of your settings file. To run the
server, use one of two ways. Either::

   (scipostenv) $ ./manage.py runserver --settings=SciPost_v1.settings.local_<name>

… or for convenience, export the same settingsfile path to the
``DJANGO_SETTINGS_MODULE`` variable, so that one can run the django
commands by default::

   (scipostenv) $ export DJANGO_SETTINGS_MODULE="SciPost_v1.settings.local_<name>"

One can of course also add this variable to your ``~/.bash_profile`` for
convenience.


****
Mail
****

In the ``mails`` application a special `Email
Backend <https://docs.djangoproject.com/en/1.11/topics/email/#email-backends>`__
is defined. This will write all emails to the database. To use this
backend, in the settings set the the variable ``EMAIL_BACKEND`` as::

   # settings.py
   EMAIL_BACKEND = 'mails.backends.filebased.ModelEmailBackend'
   EMAIL_BACKEND_ORIGINAL = 'mails.backends.filebased.EmailBackend'

A management command is defined to send the unsent mails in the
database. This management command uses the Email Backend defined in the
settings under variable ``EMAIL_BACKEND_ORIGINAL``. If not defined, this
defaults to the Django default:
``django.core.mail.backends.smtp.EmailBackend``::

   (scipostenv) $ ./manage.py send_mails


******
Checks
******

To make sure everything is set up and correctly configured, run::

   (scipostenv) $ ./manage.py check


**************
Module bundler
**************

`Webpack <https://webpack.js.org/>`__ takes care of assets in the
``scipost/static/scipost/assets`` folder.

Separate configurations are defined for development and production servers.
For development, the configuration file is ``webpack.dev.config.js``, while
for production it is ``webpack.prod.config.js``.

The file ``package.json`` defines the scripts needed to run npm below.


During development, to (re)compile all assets into
the ``static_bundles`` folder, simply run::

   (scipostenv) $ npm run webpack-dev

which makes use of the dev config file ``webpack.dev.config.js``.

While editing assets, it may be helpful to put Webpack in *watch* mode.
This will recompile your assets in real time. To do so, instead of the
above command, run::

   (scipostenv) $ npm run webpack-dev-live


On the production server, run::

    (scipostenv) $ npm run webpack-prod

which makes use of the prod config file ``webpack.prod.config.js``.

There is no need to run npm in *watch* mode (there is no reason for live
editing of assets on production).


******************
Sass and Bootstrap
******************

Styling will mainly be configured using `.scss
files <http://www.sass-lang.com/>`__ in the
``scipost/static/scipost/scss/preconfig.scss`` file, relying on
`Bootstrap v4.0.0-beta <//www.getbootstrap.com/>`__. A full list of
variables available by default can be found
`here <https://github.com/twbs/bootstrap/blob/v4-dev/scss/_variables.scss>`__.
All modules are configured in the ``.bootstraprc`` file. All modules are
disabled by default.


*************
Static assets
*************

In order to collect static files from all ``INSTALLED_APPS`` (i.e. the
assets managed by Webpack), run::

   (scipostenv) $ ./manage.py collectstatic

This will put all static files in the ``STATIC_ROOT`` folder defined in
your settings file. If needed, you can remove stale static files
through::

   (scipostenv) $ ./manage.py collectstatic --clear


*************************
Create and run migrations
*************************

Now that everything is set up, we can create the relevant tables in the
database::

   (scipostenv) $ ./manage.py migrate


******************
Create a superuser
******************

In order to use the admin site, you’ll need a superuser account, which
can be created using::

   (scipostenv) $ ./manage.py createsuperuser


*****************************
Create groups and permissions
*****************************

Groups and their respective permissions are set using the management
command::

   (scipostenv) $ ./manage.py add_groups_and_permissions


**********
Run server
**********

You are now ready to run the server::

   (scipostenv) $ ./manage.py runserver


************
Contributors
************

Users of the SciPost portal are known as Contributors and are created
through the registration form accessible from the home page.

You can create a number of users, and use the admin site to give them
various permissions through memberships of certain groups. For example,
you’ll want members of the SciPost Administrators and Editorial
Administrators groups in order to access the internal management and
editorial tools.


************
Initial data
************

If you’re working on an (almost) empty test database, you can easily
fill it using one of the built-in commands. To create a few instances
for each available object, simply run::

   (scipostenv) $ ./manage.py populate_db --all

Run the same command with the ``--help`` argument to find arguments to
create instances for individual models::

   (scipostenv) $ ./manage.py populate_db --help


*******************************
Maintaining database migrations
*******************************

Every time fields in any of the models change, a `database
migration <https://docs.djangoproject.com/en/1.11/topics/migrations/>`__
needs to be created and applied. The first documents a database change
and its inverse, the second actually changes the database.

Make sure to commit the migration to Git after applying it, so other
developers can use them.::

   (scipostenv) $ ./manage.py makemigrations
   (scipostenv) $ ./manage.py migrate


*************
Search engine
*************

`Django Haystack <https://haystacksearch.org>`__ is used to handle search queries. The search
engine needs indexing before you can use it::

   (scipostenv) $ ./manage.py update_index -u default

Models involved in searches are re-indexed using ``post_save`` signals. [TO BE UPDATED: ``celery`` setup].



*****************
Django-extensions
*****************

`django-extensions <https://github.com/django-extensions/django-extensions>`__
provide added commands like ``./manage.py shell_plus``, which preloads
all models in a shell session. Additional imports may be specified in
``settings.py`` as follows::

   SHELL_PLUS_POST_IMPORTS = (
       ('theses.factories', ('ThesisLinkFactory')),
       ('comments.factories', ('CommentFactory')),
   )
