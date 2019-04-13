*******
Servers
*******


Production server
=================

`SciPost <https://scipost.org>`_ is currently hosted at `WebFaction <https://www.webfaction.com>`_.


Git server
==========

SciPost runs its own git repository server at `code.scipost.org <https://code.scipost.org>`_.
This is a `Gitea <https://gitea.io>`_ instance hosted on the same server as production.

All codes needed to run SciPost are contained in various repositories on this server
(you will need access credentials).


Sentry issue tracking
=====================

To track issues on the production server, we use `Sentry <https://sentry.io/>`_,
current issues being listed `here <https://sentry.io/organizations/scipost/issues/?project=1427189>`_
(you will need access credentials).


Scheduled tasks monitoring
==========================

Scheduled tasks on the production server are powered by `Celery <http://www.celeryproject.org>`_.
Monitoring is done via our `Flower <https://scipost.org/flower/>`_ instance
(you will need access credentials).


Site traffic statistics
=======================

We run an `AWStats <https://www.awstats.org>`_ instance at `this page <https://scipost.org/awstats>`_.
