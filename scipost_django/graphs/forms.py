__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django import forms

from graphs.graphs.plotkind import PlotKind
from graphs.graphs.plotter import ModelFieldPlotter

from .graphs import ALL_PLOTTERS, ALL_PLOT_KINDS, AVAILABLE_MPL_THEMES

from crispy_forms.helper import FormHelper, Layout
from crispy_forms.layout import LayoutObject, Div, Field


class ModelFieldPlotterSelectForm(forms.Form):
    model_field_plotter = forms.ChoiceField(
        choices=[(None, "-" * 9)] + [(key, key.title()) for key in ALL_PLOTTERS],
        label="Model Field",
        required=False,
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


class PlotKindSelectForm(forms.Form):
    plot_kind = forms.ChoiceField(
        choices=[(None, "-" * 9)] + [(key, key.title()) for key in ALL_PLOT_KINDS],
        label="Plot kind",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If a plot kind is already selected, populate the form with its options
        plot_kind_class_name = self.data.get("plot_kind", None)
        if plot_kind_class := PlotKind.class_from_name(plot_kind_class_name):
            self.fields.update(plot_kind_class.Options.get_option_fields())

        self.kind_class = plot_kind_class


class GenericPlotOptionsForm(forms.Form):
    theme = forms.ChoiceField(
        choices=[(name, name.title()) for name in AVAILABLE_MPL_THEMES],
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


class PlotOptionsForm(forms.Form):
    """
    Combination of the model field selector, the plot kind selector, and generic plot options.
    """

    def __init__(self, *args, **kwargs):
        self.model_field_select_form = ModelFieldPlotterSelectForm(*args, **kwargs)
        self.plot_kind_select_form = PlotKindSelectForm(*args, **kwargs)
        self.generic_plot_options_form = GenericPlotOptionsForm(*args, **kwargs)

        # Update the allowed kind choices based on the selected model field plotter
        if plotter := self.model_field_select_form.plotter:
            self.plot_kind_select_form.fields["plot_kind"].choices = list(
                filter(
                    lambda x: x[0] in plotter.get_available_plot_kinds(),
                    self.plot_kind_select_form.fields["plot_kind"].choices,
                )
            )

        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout()

        self.fields.update(self.model_field_select_form.fields)
        if not plotter:
            return

        self.fields.update(self.plot_kind_select_form.fields)
        self.fields.update(self.generic_plot_options_form.fields)

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
