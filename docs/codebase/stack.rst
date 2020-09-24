##################
The tech stack
##################

Which technologies is SciPost built on?

We are strong advocates for `Free Software <https://www.gnu.org/philosophy/free-sw.html>`_
and strictly limit our tech stack choices to applications listed in the
`Free Software Directory <https://directory.fsf.org/wiki/Main_Page>`_.

SciPost rests on

* the `Python <https://www.python.org>`_ language

* with `Git <https://git-scm.com/>`_ version tracking

* and `Django <https://djangoproject.com>`_ as the core framework.

* Our APIs leverage the `Django Rest Framework <https://www.django-rest-framework.org>`_.

* Our databases are `PostgreSQL <https://www.postgresql.org>`_ instances.

* Styling makes use of `Bootstrap <https://getbootstrap.com>`_ with lots of
  custom tweaks and additions.

* Our original frontend makes use of custom
  `JavaScript <https://developer.mozilla.org/en-US/docs/Web/JavaScript>`_
  peppered with `jQuery <https://jquery.com>`_.

* For our newer frontend we are having fun using `Vue.js <https://vuejs.org>`_
  `single-file components <https://vuejs.org/v2/guide/single-file-components.html>`_
  (with `bootstrap-vue <https://bootstrap-vue.js.org>`_ for the looks),
  plugging these to our backend APIs using
  the `Requests <https://2.python-requests.org>`_ library.

* Static assets are bundled and optimized using `Webpack <https://webpack.js.org>`_.

* Mathematics is displayed using `MathJax <https://www.mathjax.org>`_.

* Scheduled tasks rely on `Celery <https://docs.celeryproject.org>`_
  with a `RabbitMQ <https://www.rabbitmq.com/>`_ broker, all monitored by a
  `Flower <https://github.com/mher/flower>`_ instance.

* Our site's
  `Content Security Policy <https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP>`_
  is implemented using
  `Mozilla's <https://github.com/mozilla>`_
  `django-csp <https://github.com/mozilla/django-csp>`_
  (check our `current report <https://securityheaders.com/?q=scipost.org&followRedirects=on>`_).

* Documentation is written in `reStructuredText <https://docutils.sourceforge.io/rst.html>`_
  and built with `Sphinx <https://www.sphinx-doc.org>`_.


Besides this, we also use

* `Sentry <https://sentry.io/>`_ for live error monitoring on our servers.


We self-host our code repositories by running

* a `GitLab <https://gitlab.com/gitlab-org/gitlab>`_ instance
  at `scipost-codebases.org <https://scipost-codebases.org>`_.

See our :doc:`deployment documentation <../deployment/index>` for the complete details
of how our services are brought to life.


While we of course make use of many other pieces of software (check the
`requirements.txt` and `package.json` files in the main repository),
we have a strong and seemingly insurmountable tendency to write our own
systems from scratch. See the extensive :doc:`list of apps <apps/index>`
we have developed over time in order to cover all our needs.
