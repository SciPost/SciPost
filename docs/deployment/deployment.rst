*****************
SciPost unleashed
*****************


This section describes how the SciPost stack
is fired up and unleashed at `scipost.org <https://scipost.org>`_.



Production server
=================

`SciPost <https://scipost.org>`_ is currently hosted at `Digital Ocean <https://www.digitalocean.com>`_.


Git server
==========

SciPost runs its own git repository server at `git.scipost.org <https://git.scipost.org>`_.
This is a `GitLab <https://gitlab.com/gitlab-org/gitlab>`_ instance hosted on a selfstanding server.

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
