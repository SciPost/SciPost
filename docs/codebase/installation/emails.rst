****************
Templated emails
****************

The ``mails`` app is used as the (templated) mailing processor of SciPost. Each email is defined using two files: the template and the configuration file.

Each mail is defined using certain general configuration possibilities. These options are defined in the json configuration file or are overwritten in the methods described below. These fields are:

`subject` {string}
  The subject of the mail.

`recipient_list` and `bcc` {list}
  Both fields are lists of strings. Each string may be either a plain mail address, eg. ` example@scipost.org`, or it may represent a certain relation to the central object. For example, one may define::

    >>> sub_1 = Submission.objects.first()
    >>> mail_util = DirectMailUtil([...], object=sub_1, recipient_list=['example@scipost.org', 'submitted_by.user.email'])


`from_email` {string}
  For this field, the same flexibility and functionality exists as for the `recipient_list` and `bcc` fields. However, this field should always be a single string entry::

    >>> mail_util = DirectMailUtil([...], from_email='noreply@scipost.org')


`from_name` {string}
  The representation of the mail sender.

Central object
==============

Using a single Model instance
-----------------------------
The "central object" is a ``django.db.models.__Model__`` instance that will be used for the email fields if needed and in the template. The mail engine will try to automatically detect a possible Model instance and save this in the template context as `<Model.verbose_name>` and `object`. The keyword you use to send it to the mail engine is not relevant for this method, but will be copied to be used in the template as well.

Example
^^^^^^^

To make a Submission available to an email template::

  >>> sub_1 = Submission.object.first()
  >>> mail_util = DirectMailUtil([...], weird_keyword=sub_1)


In the template, the variables ``weird_keyword``, ``submission`` and ``object`` will all represent the `sub_1` instance. For example::

  <h1>Dear {{ weird_keyword.submitted_by.get_title_display }} {{ object.submitted_by.user.last_name }},</h1>
  <p>Thank you for your submission: {{ submission.title }}.</p>


Using multiple Model instances
------------------------------
If a certain mail requires more than one Model instance, it is required to pass either a `instance` or `object` parameter for the mail engine to determine the central object.

Example::

  >>> sub_1 = Submission.object.first()
  >>> report_1 = Report.object.first()
  >>> mail_util = DirectMailUtil([...], submission=sub_1, report=report_1)
  ValueError: "Multiple db instances are given."


Here, it is required to pass either the ``instance`` or ``object`` parameter, eg.::

  >>> mail_util = DirectMailUtil([...], object=sub_1, report=report_1)


Configuration file
------------------

Each mail is configured with a json file, ``templates/email/*__<mail_code>.json``, which at least contains a ``subject`` and ``recipient_list`` value. The other fields are optional. An example of all available configuration fields are shown::

  {
      "subject": "Foo subject",
      "recipient_list": [
          "noreply@scipost.org"
      ],
      "bcc": [
      "secret@scipost.org"
      ],
      "from_email": "server@scipost.org",
      "from_name": "SciPost Techsupport"
  }

Template file
-------------

Any mail will be defined in the html template file ``templates/email/__<mail_code>.html`` using the conventions as per `Django's default template processor <https://docs.djangoproject.com/en/1.11/topics/templates/>`_.

Direct mail utility
===================

The fastest, easiest way to use templated emails is using the ``DirectMailUtil`` class::

   mails.utils.__DirectMailUtil(__*mail_code, delayed_processing=True, subject='', recipient_list=[], bcc=[], from_email='', from_name='', \**template_variables*__)


Attributes
----------

`mail_code` {string}
  The unique code refereeing to a template and configuration file.

`delayed_processing` {boolean, optional}
  Execute template rendering in a cronjob to reduce executing time.

`subject` {string, optional}
  Overwrite the ``subject`` field defined in the configuration field.

`recipient_list` {list, optional}
  Overwrite the ``recipient_list`` field defined in the configuration field.

`bcc` {list, optional}
  Overwrite the ``bcc`` field defined in the configuration field.

`from_email` {string, optional}
  Overwrite the `from_email` field defined in the configuration field.

`from_name` {string, optional}
  Overwrite the `from_name` field defined in the configuration field.

`**template_variables`
  Append any keyword argument that may be used in the email template.

Methods
-------

`send_mail()`
  Send the mail as defined on initialization.

Basic example
-------------

Directly sending an email::

   >>> from mails.utils import DirectMailUtil
   >>> mail_util = DirectMailUtil('test_mail_code_1')
   >>> mail_util.send_mail()

This utility is protected to prevent double sending. So now, the following has no effect anymore::

   >>> mail_util.send_mail()



Class-based view editor
=======================

This acts like a regular Django class-based view, but will intercept the post request to load the email form and submit when positively validated.

This view may be used as a `generic editing view <https://docs.djangoproject.com/en/1.11/ref/class-based-views/generic-editing/>`_ or `DetailView <https://docs.djangoproject.com/en/1.11/ref/class-based-views/generic-display/#detailview>`_.


``mails.views.MailView``
=========================

This view is a basic class-based view, which may be used as basic editor for a specific templated email.

Attributes
----------

`mail_code` {string}
  The unique code refereeing to a template and configuration file.

`mail_config` {dict, optional}
  Overwrite any of the configuration fields of the configuration file:

    * `subject` {string}
    * `recipient_list` {list}
    * `bcc` {list}
    * `from_email` {string}
    * `from_name` {string}

`mail_variables` {dict, optional}
  Append extra variables to the mail template.

`fail_silently` {boolean, optional}
  If set to ``False``, raise ``PermissionDenied`` if ``can_send_mail()`` returns False on POST request.

Methods
-------

`can_send_mail()`
  Control permission to actually send the mail. Return a boolean, returns ``True`` by default.

`get_mail_config()`
  Return an optional explicit mail configuration. Return a dictionary, returns ``mail_config`` by default.


``mails.views.MailFormView``
============================

This view may be used as a generic editing view, and will intercept the POST request to let the user edit the email before saving the original form and sending the templated mail.

Attributes
----------

`form_class` {django.forms.__ModelForm__ | django.forms.__Form__}
  The original form to use as in any regular Django editing view.

`mail_code` {string}
  The unique code refereeing to a template and configuration file.

`mail_config` {dict, optional}
  Overwrite any of the configuration fields of the configuration file:
    * `subject` {string}
    * `recipient_list` {list}
    * `bcc` {list}
    * `from_email` {string}
    * `from_name` {string}

`mail_variables` {dict, optional}
  Append extra variables to the mail template.

`fail_silently` {boolean, optional}
  If set to ``False``, raise ``PermissionDenied`` if ``can_send_mail()`` returns ``False`` on POST request.

Methods
-------

`can_send_mail()`
  Control permission to actually send the mail. Return a boolean, returns ``True`` by default.

`get_mail_config()`
  Return an optional explicit mail configuration. Return a dictionary, returns ``mail_config`` by default.


Basic example
-------------

Views file::

   # <app>/views.py
   from mails.views import MailView

   class FooView(MailView):
       mail_code = 'test_mail_code_1'

Urls file::

   # <app>/urls.py
   from django.conf.urls import url

   from .views import FooView

   urlpatterns = [
		url(r'^$', FooView.as_view(), name='foo'),
   ]



Function-based view editor
==========================

Similar to the ``MailView`` it is possible to have the user edit a templated email before sending in function-based views, using the ``MailEditorSubview``.

``mails.views.MailEditorSubview``
---------------------------------

Attributes
----------

`request` {django.http.__HttpResponse__}
  The HttpResponse which is typically the first parameter in a function-based view.

`mail_code` {string}
  The unique code refereeing to a template and configuration file.

`header_template` {string, optional}
  Any template that may be used in the header of the edit form.

`context` {dict, optional}
  A context dictionary as in any usual Django view, which may be useful combined with `header_template`.

`subject` {string, optional}
  Overwrite the `subject` field defined in the configuration field.

`recipient_list` {list, optional}
  Overwrite the `recipient_list` field defined in the configuration field.

`bcc` {list, optional}
  Overwrite the `bcc` field defined in the configuration field.

`from_email` {string, optional}
  Overwrite the `from_email` field defined in the configuration field.

`from_name` {string, optional}
  Overwrite the `from_name` field defined in the configuration field.

`**template_variables`
  Append any keyword argument that may be used in the email template.

Methods
-------

`is_valid()`
  See if data is returned and valid, similar to Django forms. Returns a __boolean__.

`interrupt()`
  Interrupt request by rendering the templated email form. Returns a `HttpResponse <https://docs.djangoproject.com/en/2.1/ref/request-response/#django.http.HttpResponse>`_.

`send_mail()`
  Send email as edited by the user in the template.


Basic example::

  from submissions.models import Submission
  from mails.views import MailEditorSubview

  def any_method_based_view(request):
      submission = Submission.objects.first()
      mail_request = MailEditorSubview(request, 'test_mail_code_1', object=submission)
      if mail_request.is_valid():
          mail_request.send_mail()
          return redirect('reverse:url')
      else:
          return mail_request.interrupt()


Important epilogue
==================

Every templated mail defined in the ``templates/email/`` folder will be tested for proper configuration. This tests includes tests on the configuration file and existence of the template. Important note: it does not test the content of the templates (read: the variables used in the template). To run these, and all other mail-related unit tests, simple run the following::

  (scipostenv) $ ./manage.py test mails.tests -k


A successful test ends by printing "OK". In any other case, errors will be raised.
