Maintenance of SciPost documentation
====================================



Sphinx-generated docs
---------------------


Generating the static html files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the `docs` subfolder, invoke ``make html``. The html files will be automatically generated and put in `build/html` subfolders.



Sphinxdoc-generated docs (viewable online)
------------------------------------------


Setting things up
~~~~~~~~~~~~~~~~~

The `django-sphinxdoc` app creates `Project` and `Document` classes. In the admin, one should create the following project (slug in parentheses):

   * SciPost developers (developers)


Updating the docs:
~~~~~~~~~~~~~~~~~~

Use the management command ``python manage.py updatedoc -b <project-slug>`` with slug `developers`.
