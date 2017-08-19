# SciPost
The complete scientific publication portal

## Dependencies
SciPost is written in Python 3.5 using Django 1.11 and requires PostgreSQL 9.4 or
higher. Python dependencies are listed in `requirements.txt`. Frontend dependencies are managed by [NPM](https://www.npmjs.com/) in package.json.

## Getting started

### Database
Make sure that PostgreSQL is installed and running and that a database with user is set up. A
good guide how to do this can be found [here](https://djangogirls.gitbooks.io/django-girls-tutorial-extensions/content/optional_postgresql_installation/) (NOTE: stop before the 'Update settings' part).

### Python version
Make sure you're using Python 3.5. You are strongly encouraged to use a [virtual environment](https://virtualenv.pypa.io/en/stable/).


```shell
$ virtualenv scipostenv --python=python3.5
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
In this project, most settings are tracked using Git. Some settings however, are still secret are and should stay that way. These settings may be saved into the  `secrets.json` file in the root of the project. The minimum required structure is as follows, please mind the non-empty, but still invalid `SECRET_KEY`:

```json
{
  "SECRET_KEY": "<key>",
  "DB_NAME": "",
  "DB_USER": "",
  "DB_PWD": ""
}
```

The settings files itself are saved into `SciPost_v1/settings/local_<name>.py`. Be sure to *wildcard import* the `base.py` file in the top of your settings file. To run the server, one can do it two ways. Either:

```shell
(scipostenv) $ ./manage.py runserver --settings=SciPost_v1.settings.local_<name>
```

...or for convenience, export the same settingsfile path to the `DJANGO_SETTINGS_MODULE` variable, so that one can run the django commands are default:

```shell
(scipostenv) $ export DJANGO_SETTINGS_MODULE="SciPost_v1.settings.local_<name>"
```

One can of course also add the variable to the `~/.bash_profile` for convenience.

### Check, double check
To make sure everything is set up and configured well, run:

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

#### Sass and bootstrap
Styling will mainly be configured using [.scss files](http://www.sass-lang.com/) in the `scipost/static/scipost/scss/preconfig.scss` file, relying on [Bootstrap v4.0.0-beta](//www.getbootstrap.com/). A full list of variables available by default can be found [here](https://github.com/twbs/bootstrap/blob/v4-dev/scss/_variables.scss).
All modules are configured in the `.bootstraprc` file; All modules are disabled by default.

### Collectstatic
In order to collect static files from all `INSTALLED_APPS`, i.e. the assets managed by Webpack, run:

```shell
(scipostenv) $ ./manage.py collectstatic
```

This will put all static files in the `STATIC_ROOT` folder defined in your settings file. It's a good idea to use the clear option in order to remove stale static files:

```shell
(scipostenv) $ ./manage.py collectstatic --clear
```

### Create and run migrations
Now that everything is setup, we can set up the datastructures.
```shell
(scipostenv) $ ./manage.py migrate
```

### Create a superuser
In order to use the admin site, you'll need a superuser account.
```shell
(scipostenv) $ ./manage.py createsuperuser
```

### Create groups and permissions
Groups and their respective permissions are set using the management command.

```shell
(scipostenv) $ ./manage.py add_groups_and_permissions
```

### Run development server
You are now ready to run the development server:

```shell
(scipostenv) $ ./manage.py runserver
```

## Contributors
Users of the portal are known as Contributors and are created through the registration form accessible from the home page.

You can create a number of users, and use the admin site to give them various permissions through memberships of certain groups. For example, you'll want members of the SciPost Administrators and Editorial Administrators groups in order to access the internal management and editorial tools.

## Initial data
If you're working on an (almost) empty database, one can easily fill its test database using one of the built-in commands. To create few instances for each available object, simply run:

```shell
(scipostenv) $ ./manage.py populate_db --all
```

Run the help argument to find arguments to create instances for individual models.

```shell
(scipostenv) $ ./manage.py populate_db --help
```


## Maintaining database migrations
Every time fields in any of the models change, a [database migration](https://docs.djangoproject.com/en/1.11/topics/migrations/)
needs to be created and applied. The first documents a database change and its
inverse, the second actually changes the database.

Make sure to commit the migration to GIT after applying it, so other developers
can use them.

```shell
(scipostenv) $ ./manage.py makemigration
(scipostenv) $ ./manage.py migrate
```

## Search engine
[Django Haystack]() is used to handle search queries. The search engine needs indexing before proper use.

```shell
(scipostenv) $ ./manage.py update_index -u default
```
Models involved in searches are re-indexed as per `post_save` signal.


## Documentation
All project documentation is gathered from `.rst` files and code-embedded docstrings.
The documentation itself can be found in `docs`.

### Sphinxdoc
The documentation is saved in the local database as a Project with name `SciPost`
(this project should be manually created in the admin under the `Sphinxdoc` app).

To update the docs, simply run
```shell
(scipostenv) $ python3 ../manage.py updatedoc -b scipost
```

The documentation is then viewable by navigating to `docs/`.


### Locally-served
The documentation can be rendered using
[Sphinx](http://www.sphinx-doc.org/). Note that rendering documentation is only
available from the virtual environment - and only when the host settings have
been configured.

To build the documentation, run:

```shell
(scipostenv) $ cd docs
(scipostenv) $ make html
```

After this, generated documentation should be available in `docs/_build/html`.

## Django-extensions
[django-extensions](https://github.com/django-extensions/django-extensions) provide added commands like
`./manage.py shell_plus`, which preloads all models in a shell session. Additional imports may be specified in `settings.py` as follows:

```python
SHELL_PLUS_POST_IMPORTS = (
    ('theses.factories', ('ThesisLinkFactory')),
    ('comments.factories', ('CommentFactory')),
)
```
