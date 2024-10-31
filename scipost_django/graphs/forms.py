__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django import forms

from graphs.graphs.plotkind import PlotKind
from graphs.graphs.plotter import ModelFieldPlotter

from .graphs import ALL_PLOTTERS, ALL_PLOT_KINDS

import matplotlib.pyplot as plt


class ModelFieldPlotterSelectForm(forms.Form):
    model_field_plotter = forms.ChoiceField(
        choices=[(key, key.title()) for key in ALL_PLOTTERS],
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
        choices=[(key, key.title()) for key in ALL_PLOT_KINDS],
        label="Plot kind",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If a plot kind is already selected, populate the form with its options
        if plot_kind := PlotKind.from_name(self.data.get("plot_kind", None), self.data):
            self.fields.update(plot_kind.Options.get_option_fields())

        self.kind = plot_kind

    def clean(self):
        cleaned_data = super().clean()

        # Recreate plot kind with cleaned data
        self.kind = PlotKind.from_name(self.data.get("plot_kind", None), cleaned_data)
        return cleaned_data


class GenericPlotOptionsForm(forms.Form):
    theme = forms.ChoiceField(
        choices=[(t, t.title()) for t in plt.style.available],
        label="Theme",
        required=False,
    )
    title = forms.CharField(label="Title", required=False)


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

        self.fields.update(self.model_field_select_form.fields)
        self.fields.update(self.plot_kind_select_form.fields)
        self.fields.update(self.generic_plot_options_form.fields)

    def clean(self):
        cleaned_data = super().clean()

        self.model_field_select_form.full_clean()
        self.plot_kind_select_form.full_clean()
        self.generic_plot_options_form.full_clean()

        return cleaned_data
