*************
Documentation
*************

As for all good Python-based projects, our documentation is written in
`reStructuredText <http://docutils.sourceforge.net/rst.html>`_. Some useful
links are:

* docutils `documentation <http://docutils.sourceforge.net/rst.html>`_ (the autoritative reST reference)
* Sphinx's `reST primer <http://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html>`_
* Python's `PEP 257 <https://www.python.org/dev/peps/pep-0257/>`_ docstring conventions
* Django's `Writing documentation guide <https://docs.djangoproject.com/en/dev/internals/contributing/writing-documentation/>`_

The source of all documentation resides in ``.rst`` files rooted in the ``docs``
folder, together with code-embedded docstrings.


Building the documentation
==========================

The documentation is compiled using
`Sphinx <http://www.sphinx-doc.org/>`__. Note that compiling
documentation occurs within the virtual environment with host settings linked.

For the apps, the .rst files are auto-generated using `sphinx apidoc <https://github.com/sphinx-contrib/apidoc>`_ through the bash script ``build_app_src.sh``.

To build the documentation, run::

  $ cd docs
  $ ./build_app_src
  $ make html

The documentation is then output to folder ``docs/_build/html`` (static html format),
and easily viewable in your browser.



Sphinxdoc [deprecated]
======================

To serve the documentation, use is made of `django-sphinxdoc <https://django-sphinxdoc.readthedocs.io/en/latest/>`_.

The documentation is saved in the local database as a Project with name
``SciPost``, with slug ``SciPost`` and path ``/docs``
(this project should be manually created in the admin under the
``Sphinxdoc`` app).

To update the docs, simply run::

   $ ./manage.py updatedoc -b SciPost

The documentation is then viewable by navigating to ``docs`` in your browser.
