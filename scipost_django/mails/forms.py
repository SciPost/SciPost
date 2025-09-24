__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import re
from typing import TYPE_CHECKING, Any
from django import forms

from common.forms import MultiEmailField
from common.utils.models import get_current_domain
from common.utils.text import split_strip
from scipost.templatetags.user_groups import is_ed_admin, is_scipost_admin

from .core import MailEngine
from .exceptions import ConfigurationError
from .widgets import SummernoteEditor

if TYPE_CHECKING:
    from django.contrib.auth.models import User


class EmailForm(forms.Form):
    """
    This form is prefilled with data from a mail_code and is used by any user to send out
    the mail after editing.
    """

    required_css_class = "required-asterisk"

    from_address = forms.ChoiceField(label="From", required=True)
    to_address = forms.MultipleChoiceField(label="To", required=True)
    subject = forms.CharField(max_length=255, label="Subject")
    text = forms.CharField(widget=SummernoteEditor, label="Text")
    cc_mail_field = MultiEmailField(label="Optional: cc this email to", required=False)
    bcc_mail_field = MultiEmailField(
        label="Optional: bcc this email to", required=False
    )
    prefix = "mail_form"
    extra_config: dict[str, Any] = {}

    def __init__(self, *args, **kwargs: Any):
        self.mail_code = kwargs.pop("mail_code")
        # Check if all exta configurations are valid.
        self.extra_config.update(kwargs.pop("mail_config", {}))

        # Pop out user to prevent saving it as a form field.
        user: "User | None" = kwargs.pop("user", None)

        if not all(key in MailEngine._parameters for key in self.extra_config):
            raise KeyError("Not all `extra_config` parameters are accepted.")

        # This form shouldn't be is_bound==True if there is any non-relevant POST data given.
        if len(args) > 0 and args[0]:
            data = args[0]
        elif "data" in kwargs:
            data = kwargs.pop("data", {})
        else:
            data = {}
        if "%s-subject" % self.prefix in data.keys():
            data = {
                f"{self.prefix}-{key}": data.get(f"{self.prefix}-{key}")
                for prefixed_key in data.keys()
                if (key := re.sub(f"^{self.prefix}-", "", prefixed_key)) != prefixed_key
                and key in self.base_fields
            }

            # Cast `to_address` to a list if it is a single string.
            # This avoids the MultipleChoiceField raising an error, when the form is bound.
            # This cannot happen in `clean_[field]` since it runs after the the default field validation.
            to_address = data.get(f"{self.prefix}-to_address", None)
            if to_address and not isinstance(to_address, list):
                data[f"{self.prefix}-to_address"] = [to_address]

        else:
            # Reset to prevent having a false-bound form.
            data = {}
        super().__init__(data or None)

        # Set the data as initials
        self.engine = MailEngine(self.mail_code, **self.extra_config, **kwargs)
        self.engine.process(render_template=True)
        config = self.engine.mail_config

        self.fields["text"].widget = SummernoteEditor(
            csp_nonce=kwargs.pop("csp_nonce", None)
        )
        self.fields["text"].initial = config.get("html_message", "")
        self.fields["subject"].initial = config.get("subject", "")

        # Determine the available from addresses passed to the form.
        # Append the default from address from the mail_code json.
        # Remove duplicates and select the default from address as initial.
        self.available_from_addresses: list[tuple[str, str]] = [
            (
                config.get("from_email", ""),
                config.get("from_name", ""),
            )
        ] + EmailForm.get_available_from_addresses_for_user(user)

        # Create choices without duplicates while preserving order.
        to_addresses = [(r, r) for r in config.get("recipient_list", [])]
        from_addresses: list[tuple[str, str]] = []
        for address, description in self.available_from_addresses:
            if address not in [a[0] for a in from_addresses]:
                from_addresses.append((address, f"{description} <{address}>"))

        self.fields["to_address"].choices = to_addresses
        self.fields["from_address"].choices = from_addresses

        for field_name in ["to_address", "from_address"]:
            choices = self.fields[field_name].choices
            select_widget = forms.Select(choices=choices)
            select_widget.attrs |= {
                "class": "form-select",
                "size": len(choices),
                "aria-label": field_name.replace("_", " ").capitalize(),
            }
            self.fields[field_name].widget = select_widget

        self.fields["to_address"].initial = config.get("recipient_list", [])
        self.fields["from_address"].initial = config.get("from_email", "")

    def clean(self):
        super().clean()
        address = self.cleaned_data.get("to_address")

        if not address:
            self.add_error("to_address", "You must select at least one recipient.")

        return self.cleaned_data

    def is_valid(self):
        """Fallback used in CBVs."""

        if super().is_valid():
            # Check that to and from addresses are provided choices.
            to_addresses: list[str] = self.cleaned_data.get("to_address", [])
            to_address_choices = dict(self.fields["to_address"].choices)
            for to_address in to_addresses:
                if to_address not in to_address_choices:
                    self.add_error(
                        "to_address",
                        f"Recipient address {to_address} not in {to_address_choices}.",
                    )

            from_address: str = self.cleaned_data.get("from_address", "")
            from_address_choices = dict(self.available_from_addresses)
            if from_address not in from_address_choices:
                self.add_error("from_address", "Sender address not in list.")

            # Push new data to the engine so it can be validated.
            old_mail_data = self.engine.mail_config_overrides
            self.engine.mail_config_overrides.update(
                {
                    "from_name": from_address_choices.get(from_address, ""),
                    "from_email": from_address,
                    "recipient_list": to_addresses,
                }
            )

            try:
                self.engine.process(render_template=False)
                return True
            except (ImportError, KeyError, ConfigurationError) as e:
                self.add_error(None, "The mail could not be validated. " + str(e))
                pass  # Fall through to the return False
            self.engine.mail_config_overrides = old_mail_data
        # Reset the mail data to the original state.
        return False

    def save(self):
        # Re-render the template after the user has edited the subject and text.
        message, html_message = self.engine.render_template(self.cleaned_data["text"])
        subject = self.engine.render_subject(self.cleaned_data["subject"])

        overrides: dict[str, Any] = {
            "html_message": html_message,
            "message": message,
            "subject": subject,
        }

        if cc_mail_str := self.cleaned_data["cc_mail_field"]:
            cc_mails = self.engine.mail_config_overrides.get("cc", [])
            overrides["cc"] = cc_mails + split_strip(cc_mail_str)

        if bcc_mail_str := self.cleaned_data["bcc_mail_field"]:
            bcc_mails = self.engine.mail_config_overrides.get("bcc", [])
            overrides["bcc"] = bcc_mails + split_strip(bcc_mail_str)

        # Push into overrides to take precedence over the template.
        self.engine.mail_config_overrides.update(overrides)

        # No need to render again, just validate and send.
        self.engine.process(render_template=False)
        self.engine.send_mail()

        return self.engine.template_variables["object"]

    @staticmethod
    def get_available_from_addresses_for_user(
        user: "User | None",
    ) -> list[tuple[str, str]]:
        """
        Determine the available from addresses based on the request user's permissions.
        Returns a list of tuples with the email address and the human readable name.
        """

        if user is None:
            return []

        addresses: list[tuple[str, str]] = []
        domain = get_current_domain()

        if is_ed_admin(user):
            addresses.append(("edadmin@" + domain, "SciPost Editorial Administration"))

        if is_scipost_admin(user):
            addresses.append(("admin@" + domain, "SciPost Administration"))

        return addresses


class HiddenDataForm(forms.Form):
    """
    Regular Django form which tranforms all fields to hidden fields.

    BE AWARE: This form may only be used for non-sensitive data!
        Any data that may not be interceptedby the used should NEVER be added to this form.
    """

    def __init__(self, form, *args, **kwargs):
        super().__init__(form.data, *args, **kwargs)
        for name, field in form.fields.items():
            self.fields[name] = field
            self.fields[name].widget = forms.HiddenInput()
