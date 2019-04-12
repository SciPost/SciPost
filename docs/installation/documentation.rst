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
documentation is only possible from withing the virtual environment,
with properly-configured host settings.

To build the documentation, run::

  $ cd docs
  $ make html

The documentation is then available in ``docs/build/html`` (static html format)
or ``docs/build/json`` (JSON format).


Sphinxdoc
=========

To serve the documentation, use is made of `django-sphinxdoc <https://django-sphinxdoc.readthedocs.io/en/latest/>`_.

The documentation is saved in the local database as a Project with name
``SciPost``, with slug ``SciPost`` and path ``/docs``
(this project should be manually created in the admin under the
``Sphinxdoc`` app).

To update the docs, simply run::

   $ ./manage.py updatedoc -b SciPost

The documentation is then viewable by navigating to ``docs`` in your browser.
