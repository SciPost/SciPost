__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import copy
import datetime
from typing import Any, TypeVar, Generic
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div
from crispy_bootstrap5.bootstrap5 import FloatingField
from django.contrib.sessions.backends.cache import SessionStore
from django.core.exceptions import ImproperlyConfigured
from django.core.validators import EmailValidator
from django.db.models import Q, Model, QuerySet
from django.forms import Form

from common.utils.text import title_to_kebab

M = TypeVar("M", bound=Model)
F = TypeVar("F", bound="Form")


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


class CrispyFormMixin(forms.Form):
    """
    Mixin for Django forms to add Crispy Forms helper initialization
    and the `get_form_layout` method.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        if layout := self.get_form_layout():
            self.helper = FormHelper() if not hasattr(self, "helper") else self.helper
            self.helper.layout = layout

    def get_form_layout(self) -> Layout:
        """Return the Crispy Forms layout for this form, if any."""
        field_cols: list[Div] = []
        for field in self.fields:
            # Skip the ordering field if there is no orderby field
            if field == "ordering" and "orderby" not in self.fields:
                continue
            field_cols.append(Div(FloatingField(field), css_class="col-12 col-md-6"))
        return Layout(Div(*field_cols, css_class="row"))


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


class SearchForm(Generic[M], forms.Form):
    queryset: QuerySet[M] | None = None
    model: type[M] | None = None

    ordering = forms.ChoiceField(
        label="Ordering",
        choices=(
            # FIXME: Emperically, the ordering appers to be reversed for dates?
            ("-", "Descending"),
            ("+", "Ascending"),
        ),
        required=False,
    )

    def apply_filter_set(
        self,
        filters: dict[str, str | None],
        none_on_empty: bool = False,
    ):
        """
        Set initial values of the form fields according to the given filter set.
        If `none_on_empty` is True, fields not in the filter set are set to None or [].
        """
        # Apply the filter set to the form
        for key in self.fields:
            if key in filters:
                self.fields[key].initial = filters[key]
            elif none_on_empty:
                if isinstance(self.fields[key], forms.MultipleChoiceField):
                    self.fields[key].initial = []
                else:
                    self.fields[key].initial = None

    def data_is_in_or_null(
        self,
        queryset: QuerySet[M],
        key: str,
        value: Any,
        implicit_all: bool = True,
    ) -> QuerySet[M]:
        """
        Filter a queryset such that the returned objects have a value for the given key
        within some set of values stored in the form's cleaned_data.

        Special considerations:
        - If the list contains a 0, then also include objects where the key is null.
        - If the list is empty, then include all objects if `implicit_all` is True.
        """
        if (serialized_vals := self.cleaned_data.get(value)) is None:
            return queryset

        has_unassigned = "0" in serialized_vals
        is_unassigned = Q(**{key + "__isnull": True})
        is_in_values = Q(
            **{key + "__in": list(filter(lambda x: x != 0, serialized_vals))}
        )

        if has_unassigned:
            return queryset.filter(is_unassigned | is_in_values)
        elif implicit_all and not serialized_vals:
            return queryset
        else:
            return queryset.filter(is_in_values)

    def get_queryset(self):
        """
        Evaluate the (base) queryset from which items will be searched.
        If no queryset is defined, try to get it from the model's default manager.

        Code partly inherited from Django's MultipleObjectMixin.get_queryset
        """
        if self.queryset is not None:
            queryset = self.queryset
        elif self.model is not None:
            queryset = self.model._default_manager.all()
        else:
            raise ImproperlyConfigured(
                "%(cls)s is missing a QuerySet. Define "
                "%(cls)s.model, %(cls)s.queryset, or override "
                "%(cls)s.get_queryset()." % {"cls": self.__class__.__name__}
            )

        return queryset

    def order_queryset(self, queryset: QuerySet[M]) -> QuerySet[M]:
        """
        Dynamically order the given queryset based on the 'orderby' and 'ordering'
        form fields, if present and valid.
        """
        if (orderby_value := self.cleaned_data.get("orderby")) and (
            ordering_value := self.cleaned_data.get("ordering")
        ):
            # Remove the + from the ordering value, causes a Django error
            ordering_value = ordering_value.replace("+", "")

            # Ordering string is built by the ordering (+/-), and the field name
            # from the orderby field split by "," and joined together
            queryset = queryset.order_by(
                *[
                    ordering_value + order_part
                    for order_part in orderby_value.split(",")
                ]
            )

        return queryset

    def filter_queryset(self, queryset: QuerySet[M]) -> QuerySet[M]:
        """
        Apply form-specific filters to the given queryset based on the form's
        cleaned_data and return the filtered queryset with only the applicable items.
        """
        raise NotImplementedError(
            "Subclasses of SearchForm must implement the filter_queryset method."
        )

    def search(self) -> QuerySet[M]:
        """
        Apply the search filters from the form to the base queryset
        and return the filtered and ordered queryset.
        """
        queryset = self.get_queryset()

        if self.is_valid():
            if hasattr(self, "save_field_options_to_session"):
                self.save_field_options_to_session()
            queryset = self.filter_queryset(queryset)
            queryset = self.order_queryset(queryset)
        else:
            queryset = queryset.none()

        return queryset

    @property
    def element_name(self) -> str:
        """Get the element name for this form, by default the kebab-case class name."""
        name = title_to_kebab(self.__class__.__name__)
        if name.endswith("-search-form"):
            name = name[: -len("-search-form")]

        return name
