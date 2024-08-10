__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import re
from typing import TYPE_CHECKING
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
    extra_config = {}

    def __init__(self, *args, **kwargs):
        self.mail_code = kwargs.pop("mail_code")
        # Check if all exta configurations are valid.
        self.extra_config.update(kwargs.pop("mail_config", {}))

        # Pop out user to prevent saving it as a form field.
        user = kwargs.pop("user", None)

        if not all(
            key in MailEngine._possible_parameters
            for key, val in self.extra_config.items()
        ):
            raise KeyError("Not all `extra_config` parameters are accepted.")

        # This form shouldn't be is_bound==True if there is any non-relevant POST data given.
        if len(args) > 0 and args[0]:
            data = args[0]
        elif "data" in kwargs:
            data = kwargs.pop("data")
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
        self.engine.validate(render_template=True)
        self.fields["text"].widget = SummernoteEditor(
            csp_nonce=kwargs.pop("csp_nonce", None)
        )
        self.fields["text"].initial = self.engine.mail_data["html_message"]
        self.fields["subject"].initial = self.engine.mail_data["subject"]

        # Determine the available from addresses passed to the form.
        # Append the default from address from the mail_code json.
        # Remove duplicates and select the default from address as initial.
        self.available_from_addresses = [
            (self.engine.mail_data["from_email"], self.engine.mail_data["from_name"])
        ] + EmailForm.get_available_from_addresses_for_user(user)

        from_addresses = []
        for address, description in self.available_from_addresses:
            if address not in [a[0] for a in from_addresses]:
                from_addresses.append((address, f"{description} <{address}>"))

        self.fields["from_address"].choices = from_addresses
        self.fields["from_address"].initial = self.engine.mail_data["from_email"]

        # Pass the recipient list to the form, changing the widget if there are multiple recipients.
        self.fields["to_address"].choices = [
            (recipient, recipient)
            for recipient in self.engine.mail_data["recipient_list"]
        ]
        self.fields["to_address"].initial = self.engine.mail_data["recipient_list"]
        if len(self.fields["to_address"].choices) > 1:
            self.fields["to_address"].widget.attrs["size"] = len(
                self.fields["to_address"].choices
            )
        else:
            select_widget = forms.Select(choices=self.fields["to_address"].choices)
            self.fields["to_address"].widget = select_widget

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
            to_addresses = self.cleaned_data.get("to_address")
            to_address_choices = dict(self.fields["to_address"].choices)
            for to_address in to_addresses:
                if to_address not in to_address_choices:
                    self.add_error(
                        f"to_address",
                        f"Recipient address {to_address} not in {to_address_choices}.",
                    )

            from_address = self.cleaned_data.get("from_address")
            from_address_choices = dict(self.available_from_addresses)
            if from_address not in from_address_choices:
                self.add_error("from_address", "Sender address not in list.")

            # Push new data to the engine so it can be validated.
            old_mail_data = self.engine.mail_data
            self.engine.mail_data.update(
                {
                    "from_name": from_address_choices.get(from_address, ""),
                    "from_email": from_address,
                    "recipient_list": to_addresses,
                }
            )

            try:
                self.engine.validate(render_template=False)
                return True
            except (ImportError, KeyError, ConfigurationError) as e:
                self.add_error(None, "The mail could not be validated. " + str(e))
                pass  # Fall through to the return False
            self.engine.mail_data = old_mail_data
        # Reset the mail data to the original state.
        return False

    def save(self):
        self.engine.render_template(self.cleaned_data["text"])
        self.engine.mail_data["subject"] = self.cleaned_data["subject"]
        if cc_mail_str := self.cleaned_data["cc_mail_field"]:
            if self.engine.mail_data["cc"]:
                self.engine.mail_data["cc"] += split_strip(cc_mail_str)
            else:
                self.engine.mail_data["cc"] = split_strip(cc_mail_str)
        if bcc_mail_str := self.cleaned_data["bcc_mail_field"]:
            self.engine.mail_data["bcc"] += split_strip(bcc_mail_str)

        self.engine.send_mail()
        return self.engine.template_variables["object"]

    @staticmethod
    def get_available_from_addresses_for_user(user: "User | None") -> list:
        """Determine the available from addresses based on the request user's permissions.

        Returns a list of tuples with the email address and the human readable name.
        """

        if user is None:
            return []

        emails = []
        domain = get_current_domain()

        if is_ed_admin(user):
            emails.append(("edadmin@" + domain, "SciPost Editorial Administration"))

        if is_scipost_admin(user):
            emails.append(("admin@" + domain, "SciPost Administration"))

        return emails


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
