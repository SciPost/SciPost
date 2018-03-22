Maintenance of SciPost documentation
====================================


Sphinx-generated docs
---------------------


Generating the static html files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the `docs` subfolders `codebase`, `admin` and `users`, invoke ``make html``. The html files will be automatically generated and put in `_build/html` subfolders.



Sphinxdoc-generated docs (viewable online)
------------------------------------------

Updating the docs:
~~~~~~~~~~~~~~~~~~

Use the management command ``python manage.py updatedoc -b <project-slug>`` with slugs `codebase`, `admin` and `users`.
