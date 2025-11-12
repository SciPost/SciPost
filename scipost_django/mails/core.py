__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from email.utils import make_msgid
from itertools import chain
from html2text import HTML2Text
import os
import json
import re

from django.conf import settings
from django.template import Context, Template
from django.core.mail import EmailMultiAlternatives
from django.db import models

from common.utils import get_current_domain
from common.utils.models import model_eval_attr

from .exceptions import ConfigurationError

from typing import Any, Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from journals.models import Journal


class MailEngine:
    """
    This engine processes the configuration and template files to be saved into the database in
    the MailLog table.
    """

    _parameters: dict[str, type] = {
        "recipient_list": list,
        "subject": str,
        "from_email": str,
        "from_name": str,
        "cc": list,
        "bcc": list,
        "html_message": str,
        "message": str,
    }
    _parameters_required = ["recipient_list", "subject"]
    _parameters_email = ["from_email", "recipient_list", "cc", "bcc"]

    _processed_template = False
    _mail_sent = False

    def __init__(
        self,
        mail_code: str,
        **kwargs: Any,
    ):
        """
        Start engine with specific mail_code. Any other keyword argument that is passed will
        be used as a variable in the mail template.

        @Arguments
        -- mail_code (str)

        @Keyword arguments
        The following arguments overwrite the default values, set in the configuration files:
        -- subject (str, optional)
        -- recipient_list (str, optional): List of email addresses or db-relations.
        -- cc (str, optional): List of email addresses or db-relations.
        -- bcc (str, optional): List of email addresses or db-relations.
        -- from_email (str, optional): Plain email address.
        -- from_name (str, optional): Display name for from address.
        """

        self.base_mail_code = mail_code
        self.mail_config = {}
        self.mail_config_overrides = {
            key: option
            for key, option in kwargs.items()
            if key in self._parameters and option
        }

        # Construct template variables, append keyword arguments, default to object instance.
        self.template_variables: dict[str, Any] = {"domain": get_current_domain()}
        self.template_variables.update(kwargs)
        self.template_variables.setdefault("object", self.get_object())

    @property
    def context(self) -> Context:
        """Return the context used for rendering the template."""
        return Context(self.template_variables)

    def __repr__(self):
        return '<%(cls)s code="%(code)s", validated=%(validated)s sent=%(sent)s>' % {
            "cls": self.__class__.__name__,
            "code": getattr(self, "mail_code", self.base_mail_code),
            "validated": hasattr(self, "mail_data"),
            "sent": self._mail_sent,
        }

    def process(self, render_template: bool = False):
        """
        Process and save the mail config.
        Prepares the MailEngine for sending the mail.
        """
        config_path, template_path = self.get_mail_template_paths(self.base_mail_code)
        config = self.load_mail_config(config_path, self.context)
        config |= self.mail_config_overrides
        config = self.process_email_parameters(config, self.template_variables)
        self.validate_mail_config(config)

        if render_template:
            template = self.load_mail_template(template_path)
            message, html = self.render_template(template, self.context)  # type: ignore

            config |= {
                "message": message,
                "html_message": html,
            }
            self._processed_template = True

        self.mail_config = config

    def render_template(self, template: str | Template, context: Context | None = None):
        """
        Render the message and html_message of the mail from a template and context.
        Returns a tuple of (message, html_message).
        """
        if isinstance(template, str):
            template = Template(template)

        # Render HTML and plain text version of the mail.
        html_message = template.render(context or self.context)
        message = HTML2Text().handle(html_message)

        return message, html_message

    def render_subject(self, subject: str, context: Context | None = None) -> str:
        """Render the subject str of the mail as if it were a template."""
        return Template(subject).render(context or self.context)

    def send_mail(self):
        """Send the mail."""
        if self._mail_sent:
            # Prevent double sending when using a Django form.
            return
        elif not hasattr(self, "mail_config"):
            raise ValueError(
                "The mail: %s could not be sent because there exists no mail_config."
                % self.base_mail_code
            )
        domain = get_current_domain()
        email = EmailMultiAlternatives(
            self.mail_config["subject"],
            self.mail_config.get("message", ""),
            "%s <%s>"
            % (
                self.mail_config.get("from_name", "SciPost"),
                self.mail_config.get("from_email", "noreply@%s" % domain),
            ),
            self.mail_config["recipient_list"],
            cc=self.mail_config["cc"],
            bcc=self.mail_config["bcc"],
            reply_to=[self.mail_config.get("from_email", "noreply@%s" % domain)],
            #! FIXME: Blatant abuse of the headers, needs reworking.
            headers={
                "delayed_processing": not self._processed_template,
                "context": self.template_variables,
                "mail_code": self.base_mail_code,
                "Message-ID": make_msgid(domain=domain),
            },
        )

        # Send html version if available
        if "html_message" in self.mail_config:
            email.attach_alternative(self.mail_config["html_message"], "text/html")

        email.send(fail_silently=False)
        self._mail_sent = True

        # Call mail_sent method on the object if it exists.
        if (object := self.get_object()) and hasattr(object, "mail_sent"):
            object.mail_sent()

    def get_mail_template_paths(self, base_mail_code: str) -> tuple[str, str]:
        """
        Find and return the most applicable path for the config and template files,
        depending on the provided base_mail_code and the object instance.
        """
        possible_codes: list[str] = [base_mail_code]
        suffixes: list[str] = []

        object = self.get_object()

        # Determine journal and add journal-specific suffixes
        journal: "Journal | None" = None
        match str(object.__class__.__name__):
            case "Submission":
                journal = object.submitted_to
            case "Journal":
                journal = object
            case "RefereeInvitation":
                journal = object.submission.submitted_to
            case _:
                journal = getattr(object, "journal", None)

        if journal:
            suffixes.append(journal.doi_label)

        for suffix in suffixes:
            possible_codes.append(f"{base_mail_code}_{suffix}")

        # Reverse the order such that the most specific code is first
        possible_codes.reverse()

        # Find and return the first existing configuration and template file
        EMAIL_TEMPLATE_PATH = f"{settings.BASE_DIR}/templates/email"
        config_path = next(
            (
                path
                for code in possible_codes
                if (path := f"{EMAIL_TEMPLATE_PATH}/{code}.json")
                and os.path.exists(path)
            )
        )
        template_path = next(
            (
                path
                for code in possible_codes
                if (path := f"{EMAIL_TEMPLATE_PATH}/{code}.html")
                and os.path.exists(path)
            )
        )

        return config_path, template_path

    def get_object(self) -> models.Model | None:
        """
        Search the template variables for a database instance named "object" or "instance",
        or any variable that is a Django model instance.
        Raise an error when multiple instances are found.
        """
        object_var = self.template_variables.get("object", None)
        instance_var = self.template_variables.get("instance", None)

        if object := object_var or instance_var:
            return object

        for variable in self.template_variables.values():
            if isinstance(variable, models.Model):
                if object is not None:
                    raise ValueError(
                        "Multiple db instances are given. "
                        "Please specify which object to use."
                    )

                object = variable

        return object

    @staticmethod
    def load_mail_config(
        mail_path: str, context: dict[str, Any] | Context | None = None
    ) -> dict[str, Any]:
        try:
            with open(mail_path, "r") as f:
                config = f.read()
                if context:
                    config = Template(config).render(context)
                return json.loads(config)
        except OSError:
            raise ImportError(
                f"Configuration file is malformed. Mail path: {mail_path}"
            )

    @staticmethod
    def load_mail_template(mail_path: str) -> Template:
        try:
            with open(mail_path, "r") as f:
                return Template(f.read())
        except OSError:
            raise ImportError(f"Template file is malformed. Mail path: {mail_path}")

    @classmethod
    def validate_mail_config(cls, mail_config: dict[str, Any]):
        """
        Validate the mail configuration dictionary.
        Specifically, this checks for:
        - Presence of all required parameters.
        - Absence of unknown parameters.
        - Correct types for all parameters.
        """
        errors: list[str] = []

        # Check that all required parameters are given
        for key in cls._parameters_required:
            if not (value := mail_config.get(key, None)):
                errors.append(f'option "{key}"={value} may not be empty (or falsey).')

        for key, option in mail_config.items():
            # Check that no unknown options are given
            if key not in cls._parameters:
                errors.append(f'option "{key}" is not recognized.')

            # Check that all option types are correct
            option_type = cls._parameters.get(key)
            if option_type and not isinstance(option, option_type):
                errors.append(
                    f'option "{key}"={option} must be of type {option_type.__name__}, '
                    f"not {type(option).__name__}."
                )

        if errors:
            raise ConfigurationError(
                f"The mail configuration is invalid: \n{'-\n'.join(errors)}"
            )

    @classmethod
    def process_email_parameters(
        cls,
        mail_config: dict[str, Any],
        object: dict[str, Any] | models.Model | None = None,
    ) -> dict[str, Any]:
        """
        Process email-related parameters in the mail configuration.
        This includes converting email containers to actual email addresses.
        """
        for key in cls._parameters_email:
            option = mail_config.get(key, [])
            addresses = cls._email_container_to_addresses(option, object)
            mail_config[key] = list(set(addresses))  # Remove duplicates

            # Flatten non-list parameters to str
            if cls._parameters.get(key) is str:
                if len(mail_config[key]) == 1:
                    mail_config[key] = mail_config[key][0]
                else:
                    raise ValueError(
                        f'Expected a single email address for "{key}", '
                        f"but got multiple/none: {mail_config[key]}"
                    )

        return mail_config

    @classmethod
    def _email_container_to_addresses(
        cls,
        container: str | Iterable[str],
        object: dict[str, Any] | models.Model | None,
    ) -> list[str]:
        """
        Processes an "email container" into a list of email addresses.
        An email container can be:
        - A single email address: "Mr Example <email@example.com>"
        - A domain prefixed email address: "<recipient>@"
        - An attribute path on the object, with optional filter functions:
          "object.attribute|filter_func:args|filter_func2"
        - A list of any of the above.
        """
        MAIL_REGEX = r"[\w\.\-'\+]+@[\w\.\-]+\.[a-zA-Z]{2,}"
        NAMED_MAIL_REGEX = rf"[^\n<]*<({MAIL_REGEX})>"
        DOMAIN_MAILBOX_REGEX = r"^[\w\.\-'\+]+@$"
        ATTRIBUTE_PATH_REGEX = r"^([\w\.]+)(?:\|([^\:]+(?:\:.+))?)*$"

        if not isinstance(container, str):
            return list(
                chain.from_iterable(
                    cls._email_container_to_addresses(entry, object)
                    for entry in container
                )
            )
        elif re.match(rf"^{MAIL_REGEX}$", container):
            return [container]
        elif m := re.match(rf"^{NAMED_MAIL_REGEX}$", container):
            return [m.group(1)]
        elif re.match(DOMAIN_MAILBOX_REGEX, container):
            return [container + get_current_domain()]
        elif m := re.match(ATTRIBUTE_PATH_REGEX, container):
            if object is None:
                raise ValueError(
                    "No object is given, so attribute paths cannot be resolved."
                )

            # Extract the attribute path and any filter functions with arguments.
            attribute_path, *filter_strs = m.groups()

            filters_and_args: list[tuple[str, tuple[str, ...]]] = []
            for filter_str in filter_strs:
                if not filter_str:
                    continue

                match filter_str.split(":"):
                    case [func, args]:
                        args = tuple(args.split(","))
                    case [func]:
                        args = ()
                    case _:
                        raise ValueError(f"Invalid filter format: {filter_str}")

                filters_and_args.append((func, args))

            # Attempt to retrieve the attribute from the object recursively.
            # If it does not exist, raise an error unless a "None" filter is applied.
            try:
                attribute = model_eval_attr(object, attribute_path)
            except AttributeError:
                # Ignore the error if applying any "None" filter functions.
                if any(f == "None" for f, _ in filters_and_args):
                    return []
                raise KeyError(
                    f"The property ({attribute_path}) does not exist on {object}."
                )

            # Apply all filters sequentially, with optional arguments.
            for filter_func, args in filters_and_args:
                if getattr(attribute, filter_func, None):
                    attribute = getattr(attribute, filter_func)(*args)

            # Attribute can now be none, or another email container
            if attribute is None:
                return []
            else:
                return cls._email_container_to_addresses(attribute, object)

        else:
            raise KeyError(f'Unknown email container format: "{container}".')
