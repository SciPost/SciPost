# SciPost
The complete scientific publication portal

## Dependencies
SciPost is written in Python 3.5 using Django and requires PostgreSQL 9.4 or
higher. Python dependencies are listed in `requirements.txt`. Frontend dependencies are managed by [NPM](https://www.npmjs.com/) in package.json.

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

### Frontend dependencies
[NPM](https://www.npmjs.com/) (version 4.0 or higher; tested on v4.1.2) will take care of frontend dependencies. To install all packages now run:

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

...or for convenience export the same settingsfile path to the `DJANGO_SETTINGS_MODULE` variable, so that one can run the django commands are default:

```shell
(scipostenv) $ export DJANGO_SETTINGS_MODULE="SciPost_v1.settings.local_<name>"
```

One can of course also add the variable to the `~/.bash_profile` for convenience.

### Check, double check
To make sure everything is setup and configured well, run:

```shell
(scipostenv) $ ./manage.py check
```

### Module bundler
[Webpack](https://webpack.js.org/) takes care of assets in the `scipost/static/scipost/assets` folder. To (re)compile all assets into the `static_bundles` folder, simply run:

```shell
(scipostenv) $ npm run webpack
```

While editing assets, it is helpful to put Webpack in _watch_ mode. This will recompile your assets every time you edit them. To do so, instead of the above command, run:

```shell
(scipostenv) $ npm run webpack-live
```

#### Sass and bootstrap
Styling will mainly be configured using [.scss files](http://www.sass-lang.com/) in the `scipost/static/scipost/scss/preconfig.scss` file, relying on [Bootstrap 4.0.0-beta.6](//v4-alpha.getbootstrap.com/). A full list of variables available by default can be found [here](https://github.com/twbs/bootstrap/blob/v4-dev/scss/_variables.scss).
All modules are configured in the `.bootstraprc` file. Most modules are disabled by default.

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
Groups and their respective permissions are created using the management command.

```shell
(scipostenv) $ ./manage.py add_groups_and_permissions
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

## Documentation
Project documentation can be found in `docs` and can be rendered using
[Sphinx](http://www.sphinx-doc.org/). Note that rendering documentation is only
available from the virtual environment - and only when the host settings have
been configured.

To build the documentation, run:

```shell
(scipostenv) $ cd docs
(scipostenv) $ make html
```

After this, generated documentation should be available in `docs/_build/html`.

## Writing tests
It is recommended, when writing tests, to use the `ContributorFactory` located in `scipost.factories`. This will
automatically generate a related user with Registered Contributor membership. Using the `Contributor` model in tests
requires loading the permissions and groups. Previously, this was done by including `fixtures = ["permissions",
"groups"]` at the top of the `TestCase`, but since these fixtures behave unpredictable and are a nuisance to keep up to
date with the actual groups and permissions, it is much better to call `add_groups_and_permissions`, located in
`common.helpers.test`, in a function named `setUp`, which runs before each test. `add_groups_and_permissions` wraps the
management command of the same name.

It is recommended, when writing tests for new models, to make use of `ModelFactory` instead of fixtures
for the same reason.

A basic example of a test might look like:
```shell
from django.contrib.auth.models import Group
from django.test import TestCase

from scipost.factories import ContributorFactory
from common.helpers.test import add_groups_and_permissions


class VetCommentaryRequestsTest(TestCase):
    def setUp(self):
        add_groups_and_permissions()
        self.contributor = ContributorFactory(user__password='test123')  # The default password is `adm1n`

    def test_example_test(self):
        group = Group.objects.get(name="Vetting Editors")
        self.contributor.user.groups.add(group)  # Assign user membership to an extra group
        self.client.login(username=self.contributor.user.username, password='test123')

        # Write your tests here

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
