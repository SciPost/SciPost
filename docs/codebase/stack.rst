##################
The tech stack
##################

Which technologies is SciPost built on?

We are strong advocates for `Free Software <https://www.gnu.org/philosophy/free-sw.html>`_
and strictly limit our tech stack choices to applications listed in the
`Free Software Directory <https://directory.fsf.org/wiki/Main_Page>`_.

* SciPost is built in `Python <https://www.python.org>`_

* The core framework is `Django <https://djangoproject.com>`_

* Our APIs harness the `Django Rest Framework <https://www.django-rest-framework.org>`_

* Our databases are `Postgresql <https://www.postgresql.org>`_ instances

* Our original frontend makes use of `jQuery <https://jquery.com>`_

* Our newer frontend is built using `Vue.js <https://vuejs.org>`_

* Static assets are bundled using `Webpack <https://webpack.js.org>`_

* Mathematics is displayed using `MathJax <https://www.mathjax.org>`_

* Scheduled tasks make use of `Celery <https://docs.celeryproject.org>`_

* Documentation is built with `Sphinx <https://www.sphinx-doc.org>`_


While we of course make use of many other pieces of software (check the
`requirements.txt` and `package.json` files in the main folder),
we have an unavoidable tendency to write our own systems from scratch.
