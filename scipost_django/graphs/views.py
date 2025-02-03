__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import io
from typing import Any
from urllib.parse import urlencode
from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.asgi import HttpRequest
from django.http import Http404
from django.shortcuts import HttpResponse, render
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page
from django.views.decorators.clickjacking import xframe_options_sameorigin

from graphs.forms import PlotOptionsForm


def graphs(request):

    premade_graph_options: list[dict[str, str]] = [
        {
            "model_field_plotter": "Submission",
            "plot_kind": "bar",
            "bar_plot_direction": "vertical",
            "bar_plot_group_key": "submission_date__year",
            "bar_plot_agg_func": "count",
            "bar_plot_order_by": "group",
            "bar_plot_ordering": "asc",
            "theme": "light",
            "title": "Submissions per year",
        },
        {
            "model_field_plotter": "Publication",
            "plot_kind": "bar",
            "bar_plot_direction": "vertical",
            "bar_plot_group_key": "publication_date__year",
            "bar_plot_agg_func": "count",
            "bar_plot_order_by": "group",
            "bar_plot_ordering": "asc",
            "theme": "light",
            "title": "Publications per year",
        },
        {
            "model_field_plotter": "Subsidy",
            "plot_kind": "map",
            "map_plot_country_key": "organization__country",
            "map_plot_agg_value_key": "amount",
            "map_plot_agg_func": "sum",
            "theme": "light",
            "title": "Subsidy income per country",
        },
        {
            "model_field_plotter": "PubFrac",
            "plot_kind": "map",
            "map_plot_country_key": "organization__country",
            "map_plot_agg_value_key": "cf_value",
            "map_plot_agg_func": "sum",
            "theme": "light",
            "title": "Publication expenditures per affiliation country",
        },
    ]

    premade_graphs = [
        {
            "title": options.get("title", "Graph"),
            "plot_svg": form.plot_as_svg,
            "explore_url": form.explorer_minimal_url,
        }
        for options in premade_graph_options
        if (form := PlotOptionsForm(options))
    ]

    return TemplateResponse(
        request,
        "graphs/graphs.html",
        {"premade_graphs": premade_graphs},
    )


@login_required
@permission_required("scipost.can_explore_graphs", raise_exception=True)
def explorer(request):
    form = PlotOptionsForm(request.POST or request.GET or None)
    return render(
        request,
        "graphs/explorer.html",
        {"form": form},
    )


@method_decorator(
    permission_required("scipost.can_explore_graphs", raise_exception=True),
    name="dispatch",
)
@method_decorator(xframe_options_sameorigin, name="dispatch")
class PlotView(View):
    """
    A view that renders a plot of a model.
    """

    # Modify the dispatch method to cache the page for 15 minutes
    # unless the `refresh` query parameter is set to `true`
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        method = (
            super().dispatch
            if request.GET.get("refresh")
            else cache_page(15 * 60)(super().dispatch)
        )

        return method(request, *args, **kwargs)

    def render_to_response(self, context):
        response = TemplateResponse(self.request, "graphs/plot.html", context)

        # Replace the URL in the browser history with the current plot options
        # so that the user can refresh the page without losing the current plot
        # and share the URL with others to provide a direct link to the plot
        response["HX-Replace-URL"] = self.form.explorer_minimal_url

        return response

    def get(self, request):
        form = PlotOptionsForm(request.GET)
        self.form = form

        if not form.is_valid() and request.GET.get("embed"):
            return HttpResponse("Invalid plot options: " + str(form.errors))

        self.plotter = form.model_field_select_form.plotter
        self.kind = form.plot_kind_select_form.kind_class(
            options=form.plot_kind_select_form.cleaned_data,
            plotter=self.plotter,
        )

        if request.GET.get("download"):
            return self.download(request.GET.get("download", "svg"))

        return self.render_to_response(self.get_context_data())

    def download(self, file_type):

        figure = self.form.render_figure()
        bytes_io = io.BytesIO()

        if figure is None:
            raise Http404("No figure exists with the given options")

        match file_type:
            case "svg":
                figure.savefig(bytes_io, format="svg")
                response = HttpResponse(
                    bytes_io.getvalue(), content_type="image/svg+xml"
                )

            case "png":
                figure.savefig(bytes_io, format="png", dpi=300)
                response = HttpResponse(bytes_io.getvalue(), content_type="image/png")

            case "pdf":
                figure.savefig(bytes_io, format="pdf")
                response = HttpResponse(
                    bytes_io.getvalue(), content_type="application/pdf"
                )

            case "jpg":
                figure.savefig(bytes_io, format="jpg", dpi=300)
                response = HttpResponse(bytes_io.getvalue(), content_type="image/jpg")

            case "csv":
                x, y = self.kind.get_data()

                # Write the data to a CSV file
                csv = io.StringIO()
                csv.write("x,y\n")
                for i in range(len(x)):
                    csv.write(f"{x[i]},{y[i]}\n")
                csv.seek(0)
                response = HttpResponse(csv, content_type="text/csv")

            case _:
                raise ValueError(f"Invalid file type: {file_type}")

        response["Content-Disposition"] = f"attachment; filename=plot.{file_type}"

        return response

    def get_context_data(self, **kwargs):
        return {
            "plot_svg": self.form.plot_as_svg,
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
