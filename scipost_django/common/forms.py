__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import copy
import datetime
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from django.contrib.sessions.backends.cache import SessionStore
from django.core.validators import EmailValidator


class HTMXInlineCRUDModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper() if not hasattr(self, "helper") else self.helper
        self.helper.form_tag = False


class ModelChoiceFieldwithid(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return "%s (id = %i)" % (super().label_from_instance(obj), obj.id)


class MultiEmailValidator(EmailValidator):
    def __call__(self, mail_str: str):
        for email in mail_str.split(","):
            super().__call__(email.strip())


# Should not be an Email field because browser validation is unwanted.
class MultiEmailField(forms.CharField):
    default_validators = [MultiEmailValidator()]


##### HTMX Class Based Forms #####
class HTMXDynSelWidget(forms.Select):
    template_name = "htmx/dynsel.html"

    def __init__(self, attrs=None, choices=(), **kwargs):
        self.url = kwargs.pop("url", {})
        super().__init__(attrs, choices, **kwargs)

        self.attrs = self.attrs | {
            "onclick": "return false;",
            "onkeydown": "return false;",
            "tabindex": "-1",
        }

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["url"] = self.url
        return context

    def filter_choices_to_render(self, selected_choices):
        """Replace self.choices with selected_choices."""
        if hasattr(self.choices, "queryset"):
            try:
                self.choices.queryset = self.choices.queryset.filter(
                    pk__in=[c for c in selected_choices if c]
                )
            except ValueError:
                # if selected_choices are invalid, do nothing
                pass
        else:
            self.choices = [c for c in self.choices if str(c[0]) in selected_choices]

    def optgroups(self, name, value, attrs=None):
        """
        Exclude unselected self.choices before calling the parent method.

        Used by Django>=1.10.
        """
        # Filter out None values, not needed for autocomplete
        selected_choices = [str(c) for c in value if c]
        all_choices = copy.copy(self.choices)

        self.filter_choices_to_render(selected_choices)

        result = super().optgroups(name, value, attrs)
        self.choices = all_choices

        return result


class CrispyFormMixin:
    """
    Mixin for Django forms to add Crispy Forms helper initialization
    and the `get_form_layout` method.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        if layout := self.get_form_layout():
            self.helper = FormHelper() if not hasattr(self, "helper") else self.helper
            self.helper.layout = layout

    def get_form_layout(self) -> Layout | None:
        """Return the Crispy Forms layout for this form, if any."""
        return None


class FormOptionsStorageMixin(forms.Form):
    """
    Mixin for Django forms to store and retrieve earlier selected field options
    in/from the session store.
    """

    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ):
        self.form_id: str | None = (
            kwargs.pop("form_id", None) or self.__class__.__name__
        )
        self.session_key: str | None = kwargs.pop("session_key", None)
        super().__init__(*args, **kwargs)

    def get_session_field_key(self, field_key: str) -> str:
        """Get the (form-id-prefixed) field key to be used in the session store."""
        if form_id := getattr(self, "form_id", None):
            return f"{form_id}_{field_key}"

        return field_key

    def get_session_store(self) -> SessionStore | None:
        """Get the session store associated with this form, if any."""
        if (session_key := getattr(self, "session_key", None)) is None:
            return None

        return SessionStore(session_key=session_key)

    def save_field_options_to_session(self):
        """Save the current field options to the session store."""
        if (session_store := self.get_session_store()) is None:
            return

        for field_key in self.cleaned_data:
            session_key = self.get_session_field_key(field_key)

            if field_value := self.cleaned_data.get(field_key):
                if isinstance(field_value, datetime.date):
                    field_value = field_value.strftime("%Y-%m-%d")

            session_store[session_key] = field_value

        session_store.save()

    def load_field_options_from_session(self):
        """Load field options from the session store and set them as initial values."""
        if (session_store := self.get_session_store()) is None:
            return

        for field_key in self.fields:
            session_key = self.get_session_field_key(field_key)
            if session_value := session_store.get(session_key):
                self.fields[field_key].initial = session_value

