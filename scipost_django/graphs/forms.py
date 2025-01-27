__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import io
from django import forms

from graphs.graphs.plotkind import PlotKind
from graphs.graphs.plotter import ModelFieldPlotter

from .graphs import ALL_PLOTTERS, ALL_PLOT_KINDS, AVAILABLE_MPL_THEMES

from crispy_forms.helper import FormHelper, Layout
from crispy_forms.layout import LayoutObject, Div, Field


### DANGER ZONE ###
# The following class is a subclass / modification of Django code to cater for this specific use case.
# DO NOT USE this in other places unless you know what you are doing.
class InitialCoalescedForm(forms.Form):
    """
    Modified Form that uses InitialCoalescedBoundField instead of BoundField.
    """

    class InitialCoalescedBoundField(forms.BoundField):
        """
        Modified BoundField that coalesces the initial value with the data value if the latter is not None.
        """

        def value(self):
            """
            Return the value for this BoundField:
            - `data` when the from is bound and data is not None,
            - `initial` value otherwise.
            """
            data = self.initial
            ### MODIFICATION: Coalesce the initial value with the data value if the latter is not None.
            if self.form.is_bound and self.data is not None:
                data = self.field.bound_data(self.data, data)
            return self.field.prepare_value(data)

    def __getitem__(self, name):
        """Return a BoundField with the given name."""
        try:
            field = self.fields[name]
        except KeyError:
            raise KeyError(
                "Key '%s' not found in '%s'. Choices are: %s."
                % (
                    name,
                    self.__class__.__name__,
                    ", ".join(sorted(self.fields)),
                )
            )
        if name not in self._bound_fields_cache:
            ### MODIFICATION: Use InitialCoalescedBoundField instead of BoundField
            self._bound_fields_cache[name] = (
                InitialCoalescedForm.InitialCoalescedBoundField(self, field, name)
            )
        return self._bound_fields_cache[name]


class ModelFieldPlotterSelectForm(InitialCoalescedForm):
    model_field_plotter = forms.ChoiceField(
        choices=[(None, "-" * 9)] + [(key, key.title()) for key in ALL_PLOTTERS],
        label="Model Field",
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If a model field plotter is already selected, populate the form with its options
        if plotter := ModelFieldPlotter.from_name(
            self.data.get("model_field_plotter", None), self.data
        ):
            self.fields.update(plotter.Options.get_option_fields())

        self.plotter = plotter

    def clean(self):
        cleaned_data = super().clean()

        # Recreate plotter with cleaned data
        self.plotter = ModelFieldPlotter.from_name(
            self.data.get("model_field_plotter", None), cleaned_data
        )
        return cleaned_data


class PlotKindSelectForm(InitialCoalescedForm):
    plot_kind = forms.ChoiceField(
        choices=[(None, "-" * 9)] + [(key, key.title()) for key in ALL_PLOT_KINDS],
        label="Plot kind",
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If a plot kind is already selected, populate the form with its options
        plot_kind_class_name = self.data.get("plot_kind", None)
        if plot_kind_class := PlotKind.class_from_name(plot_kind_class_name):
            self.fields.update(plot_kind_class.Options.get_option_fields())

        self.kind_class = plot_kind_class


class GenericPlotOptionsForm(InitialCoalescedForm):
    theme = forms.ChoiceField(
        choices=[(name, name.title()) for name in AVAILABLE_MPL_THEMES],
        initial="light",
        label="Theme",
        required=False,
    )
    title = forms.CharField(label="Title", required=False)
    fig_height = forms.FloatField(
        label="Height", required=False, initial=4, min_value=1, max_value=30
    )
    fig_width = forms.FloatField(
        label="Width", required=False, initial=6, min_value=1, max_value=30
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(Field("theme"), css_class="col-12"),
            Div(Field("title"), css_class="col-12"),
            Div(Field("fig_height"), css_class="col-6"),
            Div(Field("fig_width"), css_class="col-6"),
        )


class PlotOptionsForm(InitialCoalescedForm):
    """
    Combination of the model field selector, the plot kind selector, and generic plot options.
    """

    FIELD_ADMISSIBLE_TYPES: dict[str, list[str]] = {
        "value_key": ["int", "float", "date"],
        "agg_value_key": ["int", "float"],
        "timeline_key": ["date", "datetime"],
        "group_key": ["str", "int", "country"],
        "country_key": ["country"],
    }

    def __init__(self, *args, **kwargs):
        self.model_field_select_form = ModelFieldPlotterSelectForm(*args, **kwargs)
        self.plot_kind_select_form = PlotKindSelectForm(*args, **kwargs)
        self.generic_plot_options_form = GenericPlotOptionsForm(*args, **kwargs)

        # Update the allowed kind choices based on the selected model field plotter
        if plotter := self.model_field_select_form.plotter:
            plot_kind_select = self.plot_kind_select_form.fields["plot_kind"]
            plot_kind_choices = [
                (key, display_str)
                for key, display_str in plot_kind_select.choices
                if key in plotter.get_available_plot_kinds() or key is None
            ]
            plot_kind_select.choices = plot_kind_choices

        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout()

        self.fields.update(self.model_field_select_form.fields)
        if not plotter:
            return

        self.fields.update(self.plot_kind_select_form.fields)
        self.fields.update(self.generic_plot_options_form.fields)

        # Populate empty choice fields with plotter's `model_fields`
        available_model_fields: tuple[tuple[str, tuple[str, str]]] | None = (
            plotter.Options.model_fields
        )
        for field_name, field in self.fields.items():
            unprefixed_field_name = (
                self.plot_kind_select_form.kind_class.Options.unprefixed(field_name)
            )
            if (
                isinstance(field, forms.ChoiceField)
                and not field.choices
                and available_model_fields is not None
            ):
                field.choices = [
                    (key, display_str)
                    for key, (value_type, display_str) in available_model_fields
                    if value_type
                    in self.FIELD_ADMISSIBLE_TYPES.get(unprefixed_field_name, [])
                    and not (key == "id" and unprefixed_field_name == "group_key")
                ]

        def get_layout_field_names(layout: Layout):
            """Recurse through a layout to get all field names."""
            field_names: list[str] = []
            field: LayoutObject | str
            for field in layout:
                if isinstance(field, str):
                    field_names.append(field)
                else:
                    field_names.extend(get_layout_field_names(field.fields))
            return field_names

        def prefix_layout_fields(prefix: str, field: LayoutObject):
            """
            Recursively prefix the fields in a layout.
            Return type is irrelevant, as it modifies the argument directly.
            """

            if (contained_fields := getattr(field, "fields", None)) is None:
                return

            # If the crispy field is a Field type with a single string identifier, prefix it
            if (
                isinstance(field, Field)
                and len(contained_fields) == 1
                and isinstance(field_key := contained_fields[0], str)
            ):
                field.fields = [prefix + field_key]
            else:
                [prefix_layout_fields(prefix, f) for f in contained_fields]

        # Iterate over all forms and construct the form layout
        # either by extending the layout with the preferred layout from the object class
        # or by creating a row with all fields that are not already in the layout
        form: forms.Form
        object_class: ModelFieldPlotter | PlotKind | None
        for form, object_class in {
            self.model_field_select_form: self.model_field_select_form.plotter.__class__,
            self.plot_kind_select_form: self.plot_kind_select_form.kind_class,
            self.generic_plot_options_form: None,
        }.items():

            # If the form already has a layout, append it to the dynamic layout
            if helper := getattr(form, "helper", None):
                self.helper.layout.append(helper.layout)
                continue

            # Otherwise, construct a layout from the form fields
            layout = Layout()
            if object_class not in (None, None.__class__):

                # Add the principal field to the layout
                # This is usually the selector that will determine the other option fields
                principal_field_name = next(iter(form.fields.keys()))
                layout.append(Div(Field(principal_field_name), css_class="col-12"))

                get_row_field_layout = getattr(
                    object_class, "get_plot_options_form_layout_row_content", None
                )
                if get_row_field_layout:
                    try:
                        object_class_prefix = str(object_class.Options.prefix) or ""
                    except AttributeError:
                        object_class_prefix = ""

                    layout_fields = get_row_field_layout()
                    # In-place prefixing of the layout-field names
                    prefix_layout_fields(object_class_prefix, layout_fields)
                    layout.extend(layout_fields)

            layout.extend(
                [
                    Div(Field(field_name), css_class="col-12")
                    for field_name in form.fields.keys()
                    if field_name not in get_layout_field_names(layout)
                ],
            )

            self.helper.layout.append(layout)

        self.helper.all().wrap(Div, css_class="row")

    def clean(self):
        cleaned_data = super().clean()

        self.model_field_select_form.full_clean()
        self.plot_kind_select_form.full_clean()
        self.generic_plot_options_form.full_clean()

        return cleaned_data

    @property
    def options(self):
        if plot_options := getattr(self, "plot_options", None):
            return plot_options

        self.plot_options = {
            "plot_kind": {},
            "model_field_plotter": {},
            "generic": {},
        }
        for field_name, field in self.fields.items():
            clean_field_data = self.cleaned_data.get(field_name, field.initial)
            if field_name in self.model_field_select_form.fields:
                self.plot_options["model_field_plotter"][field_name] = clean_field_data
            elif field_name in self.plot_kind_select_form.fields:
                self.plot_options["plot_kind"][field_name] = clean_field_data
            else:
                self.plot_options["generic"][field_name] = clean_field_data

        return self.plot_options

    def render_figure(self):
        """
        Return a matplotlib figure based on the form data,
        or None if the form data is invalid.
        """
        if not self.is_valid():
            return None

        if not (plotter := self.model_field_select_form.plotter):
            return None

        kind = self.plot_kind_select_form.kind_class(
            options=self.plot_kind_select_form.cleaned_data,
            plotter=plotter,
        )

        return plotter.plot(kind, options=self.options.get("generic", {}))

    @property
    def plot_as_svg(self):
        """
        Return the SVG representation of the plot.
        """
        plot_svg = None
        if figure := self.render_figure():
            plot_svg = io.StringIO()
            figure.savefig(plot_svg, format="svg")
            plot_svg = plot_svg.getvalue()

            # Manipulate the SVG to make it display properly in the browser
            # Add the classes `w-100` and `h-100` to make the SVG responsive
            plot_svg = plot_svg.replace("<svg ", '<svg class="w-100 h-auto" ')

        return plot_svg
