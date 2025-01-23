__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import io
from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404
from django.shortcuts import HttpResponse, render
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page
from django.views.decorators.clickjacking import xframe_options_sameorigin

from graphs.forms import PlotOptionsForm
from scipost.permissions import HTMXResponse


@login_required
@permission_required("scipost.can_preview_new_features", raise_exception=True)
def graphs(request):

    form = PlotOptionsForm(request.POST or None)
    return render(
        request,
        "graphs/graphs.html",
        {"form": form},
    )


@method_decorator(
    permission_required("scipost.can_preview_new_features", raise_exception=True),
    name="dispatch",
)
@method_decorator(xframe_options_sameorigin, name="dispatch")
@method_decorator(cache_page(60 * 15), name="dispatch")
class PlotView(View):
    """
    A view that renders a plot of a model.
    """

    def render_to_response(self, context):
        return TemplateResponse(self.request, "graphs/plot.html", context)

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

        figure = self.render_figure()
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

    def render_figure(self):
        if not self.plotter or not self.kind:
            return None

        return self.plotter.plot(self.kind, options=self.form.options["generic"])

    def get_context_data(self, **kwargs):
        plot_svg = None
        if figure := self.render_figure():
            plot_svg = io.StringIO()
            figure.savefig(plot_svg, format="svg")
            plot_svg = plot_svg.getvalue()

            # Manipulate the SVG to make it display properly in the browser
            # Add the classes `w-100` and `h-100` to make the SVG responsive
            plot_svg = plot_svg.replace("<svg ", '<svg class="w-100 h-auto" ')

        return {
            "plot_svg": plot_svg,
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
