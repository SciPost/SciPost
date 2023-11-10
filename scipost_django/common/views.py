__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from typing import Any, Dict
from django.contrib import messages
from django.db.models.query import QuerySet
from django.forms.forms import BaseForm
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.generic import CreateView, FormView, ListView
from .forms import HTMXInlineCRUDModelForm


class HTMXInlineCRUDModelFormView(FormView):
    template_name = "htmx/htmx_inline_crud_form.html"
    form_class = HTMXInlineCRUDModelForm
    instance_li_template_name = None
    target_element_id = "htmx-crud-{instance_type}-{instance_id}"
    edit = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance_type = self.form_class.Meta.model.__name__.lower()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["target_element_id"] = self.get_target_element_id()
        context["instance_li_template_name"] = self.instance_li_template_name
        context["instance_type"] = self.instance_type
        context[self.instance_type] = context["instance"] = self.instance
        return context

    def post(self, request, *args, **kwargs):
        self.instance = get_object_or_404(self.form_class.Meta.model, pk=kwargs["pk"])
        self.edit = True
        return super().post(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.instance = get_object_or_404(self.form_class.Meta.model, pk=kwargs["pk"])
        self.edit = bool(request.GET.get("edit", None))
        super().get(request, *args, **kwargs)
        return render(request, self.template_name, self.get_context_data(**kwargs))

    def delete(self, request, *args, **kwargs):
        self.instance = get_object_or_404(self.form_class.Meta.model, pk=kwargs["pk"])
        self.instance.delete()
        messages.success(
            self.request, f"{self.instance_type.title()} deleted successfully"
        )
        return empty(request)

    def get_form(self) -> BaseForm:
        if self.request.method == "GET" and not self.edit:
            return None
        return super().get_form()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"instance": self.instance})
        return kwargs

    def get_target_element_id(self) -> str:
        return self.target_element_id.format(
            instance_type=self.instance_type,
            instance_id=self.instance.id,
        )

    def get_success_url(self) -> str:
        return self.get_context_data()["view"].request.path

    def form_valid(self, form: BaseForm) -> HttpResponse:
        form.save()
        messages.success(
            self.request, f"{self.instance_type.title()} saved successfully"
        )
        return super().form_valid(form)


class HTMXInlineCRUDModelListView(ListView):
    template_name = "htmx/htmx_inline_crud_list.html"
    add_form_class = None
    model = None
    model_form_view_url = None

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.instance_type = self.model.__name__.lower()

    def _append_model_form_view_url(self, queryset: QuerySet, **kwargs) -> QuerySet:
        for object in queryset:
            kwargs.update({"pk": object.pk})
            object.model_form_view_url = reverse(
                self.model_form_view_url, kwargs=kwargs
            )

        return queryset

    def post(self, request, *args, **kwargs):
        """
        Post requests to the list view are treated as new object creation requests.
        """
        if self.add_form_class is None:
            return empty(request)

        add_form = self.add_form_class(request.POST or None, **kwargs)

        if add_form.is_valid():
            object = add_form.save()
            kwargs.update({"pk": object.pk})

            messages.success(self.request, f"{self.instance_type.title()} successfully")

            return redirect(reverse(self.model_form_view_url, kwargs=kwargs))
        else:
            response = TemplateResponse(
                request,
                "htmx/htmx_inline_crud_new_form.html",
                {
                    "list_url": request.path,
                    "add_form": add_form,
                    "instance_type": self.instance_type,
                },
            )

            # Modify headers to swap in place with "HX-Reswap": "outerHTML"
            # This will avoid duplication of the form if errors are present
            response["HX-Reswap"] = "outerHTML"

            return response

    def get_context_data(self, **kwargs: Any):
        context = super().get_context_data(**kwargs)
        context["list_url"] = self.request.path
        context["instance_type"] = self.instance_type
        return context


def empty(request):
    return HttpResponse("")
