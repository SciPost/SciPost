__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import base64
import io
from django.shortcuts import render
from django.template.response import TemplateResponse
from django.views import View

from graphs.forms import PlotOptionsForm
from scipost.permissions import HTMXResponse


# Create your views here.
def graphs(request):

    form = PlotOptionsForm(request.POST or None)
    return render(
        request,
        "graphs/graphs.html",
        {"form": form},
    )


class PlotView(View):
    """
    A view that renders a plot of a model.
    """

    def render_to_response(self, context):
        return TemplateResponse(self.request, "graphs/plot.html", context)

    def get(self, request):
        form = PlotOptionsForm(request.GET)

        if not form.is_valid():
            return HTMXResponse(
                "Invalid plot options: " + str(form.errors), tag="danger"
            )

        cleaned_data = form.clean()

        self.plotter = form.model_field_select_form.plotter
        self.kind = form.plot_kind_select_form.kind

        self.plot_options = {
            "plot_kind": {},
            "model_field_plotter": {},
            "generic": {},
        }
        for option, value in cleaned_data.items():
            for option_group_name, option_group in self.plot_options.items():
                if option.startswith(option_group_name + "_"):
                    option_group[option] = value
                else:
                    self.plot_options["generic"][option] = value

        return self.render_to_response(self.get_context_data())

    def render_figure(self):
        if not self.plotter or not self.kind:
            return None

        return self.plotter.plot(self.kind, options=self.plot_options["generic"])

    def get_context_data(self, **kwargs):
        plot_base64 = None
        if figure := self.render_figure():
            temp_file_bytes = io.BytesIO()
            figure.savefig(temp_file_bytes)
            plot_base64 = base64.b64encode(temp_file_bytes.getvalue()).decode()

        return {
            "plot_base64": plot_base64,
            "plotter": self.plotter,
            "kind": self.kind,
            "request": self.request,
        }


class PlotOptionsFormView(View):

    def post(self, request):
        plot_options_form = PlotOptionsForm(request.POST)

        return TemplateResponse(
            request,
            "graphs/plot_options_form.html",
            {"form": plot_options_form},
        )
