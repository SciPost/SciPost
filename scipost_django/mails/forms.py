__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from common.forms import MultiEmailField

from .core import MailEngine
from .exceptions import ConfigurationError
from .widgets import SummernoteEditor


class EmailForm(forms.Form):
    """
    This form is prefilled with data from a mail_code and is used by any user to send out
    the mail after editing.
    """

    subject = forms.CharField(max_length=255, label="Subject*")
    text = forms.CharField(widget=SummernoteEditor, label="Text*")
    mail_field = MultiEmailField(label="Optional: bcc this email to", required=False)
    prefix = "mail_form"
    extra_config = {}

    def __init__(self, *args, **kwargs):
        self.mail_code = kwargs.pop("mail_code")

        # Check if all exta configurations are valid.
        self.extra_config.update(kwargs.pop("mail_config", {}))

        if not all(
            key in MailEngine._possible_parameters
            for key, val in self.extra_config.items()
        ):
            raise KeyError("Not all `extra_config` parameters are accepted.")

        # This form shouldn't be is_bound==True is there is any non-relavant POST data given.
        if len(args) > 0 and args[0]:
            data = args[0]
        elif "data" in kwargs:
            data = kwargs.pop("data")
        else:
            data = {}
        if "%s-subject" % self.prefix in data.keys():
            data = {
                "%s-subject" % self.prefix: data.get("%s-subject" % self.prefix),
                "%s-text" % self.prefix: data.get("%s-text" % self.prefix),
                "%s-mail_field" % self.prefix: data.get("%s-mail_field" % self.prefix),
            }
        else:
            # Reset to prevent having a false-bound form.
            data = {}
        super().__init__(data or None)

        # Set the data as initials
        self.engine = MailEngine(self.mail_code, **self.extra_config, **kwargs)
        self.engine.validate(render_template=True)
        self.fields["text"].widget = SummernoteEditor(
            csp_nonce=kwargs.pop("csp_nonce", "Hello!")
        )
        self.fields["text"].initial = self.engine.mail_data["html_message"]
        self.fields["subject"].initial = self.engine.mail_data["subject"]

    def is_valid(self):
        """Fallback used in CBVs."""
        if super().is_valid():
            try:
                self.engine.validate(render_template=False)
                return True
            except (ImportError, KeyError, ConfigurationError):
                return False
        return False

    def save(self):
        self.engine.render_template(self.cleaned_data["text"])
        self.engine.mail_data["subject"] = self.cleaned_data["subject"]
        if bcc_mail_str := self.cleaned_data["mail_field"]:
            self.engine.mail_data["bcc"] += [m.strip() for m in bcc_mail_str.split(",")]
        self.engine.send_mail()
        return self.engine.template_variables["object"]


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
