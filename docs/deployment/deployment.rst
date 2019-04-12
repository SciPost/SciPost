*******
Servers
*******


Production server
=================

`SciPost <https://scipost.org>`_ is currently hosted at WebFaction.


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

Monitoring of scheduled tasks on the production server is done via
a `Flower <https://scipost.org/flower/>`_ instance (you will need access credentials).
