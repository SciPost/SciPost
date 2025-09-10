__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import json
from typing import Any, Dict
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models.base import Model as Model
from django.db.models.query import QuerySet
from django.forms import formset_factory, modelformset_factory
from django.forms.forms import BaseForm
from django.forms.formsets import ManagementForm
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.html import format_html
from django.views import View
from django.views.generic import FormView, ListView
from django.views.generic.detail import SingleObjectMixin

from django_celery_results.models import TaskResult

from scipost.permissions import HTMXResponse

from .forms import HTMXInlineCRUDModelForm


def empty(request):
    return HttpResponse("")


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


class HXDynselSelectOptionView(View):
    def get(self, request, content_type_id, object_id):
        obj = self.get_object(content_type_id, object_id)

        return HttpResponse(
            format_html('<option value="{}" selected>{}</option>', obj.pk, str(obj))
        )

    def get_object(self, content_type_id, object_id):
        model = ContentType.objects.get_for_id(content_type_id).model_class()
        if model is None:
            raise ValueError("Model not found")
        return get_object_or_404(model, pk=object_id)


class HXDynselAutocomplete(View):
    model = None
    template_name = "htmx/dynsel_list_page.html"
    paginate_by = 16

    def get(self, request):
        self.page_nr = request.GET.get("page")
        self.q = request.GET.get("q", "")

        context = self.get_context_data()

        return self.render_to_response(context)

    def get_page_obj(self, page_nr):
        paginator = Paginator(self.get_queryset(), self.paginate_by)
        page_obj = paginator.get_page(page_nr)

        return page_obj

    def get_queryset(self):
        result = self.search(
            self.model.objects.all(),
            self.q,
        )
        return result

    def render_to_response(self, context):
        return TemplateResponse(
            self.request,
            self.template_name,
            context,
        )

    def search(self, queryset, q):
        return queryset

    def get_context_data(self, **kwargs):
        context = {}
        context["model_name"] = self.model._meta.verbose_name_plural
        context["q"] = self.q
        context["page_obj"] = self.get_page_obj(self.page_nr)

        return context


class HXFormSetView(View):
    """
    Class-based view for handling formsets with HTMX.
    """

    form_class = None
    formset_prefix = "formset"
    template_name = "htmx/formset_form.html"
    template_name_form = "htmx/crispy_form.html"

    def get_initial(self):
        """
        Return the initial form instances to be used in the formset if pre-existing data is available.
        Does not set the initial data for each new form.
        """
        return []

    def get_form_kwargs(self):
        return {"initial": {}}

    def get_factory_kwargs(self):
        return {}

    def get_formset_kwargs(self):
        kwargs: dict[str, Any] = {
            "form_kwargs": self.get_form_kwargs(),
        }

        if self.request.method in ("POST", "PUT"):
            kwargs.update(
                {
                    "data": self.request.POST,
                    "files": self.request.FILES,
                }
            )
        return kwargs

    def get_formset(self, data=None):
        # Determine if the formset is modelformset or regular formset
        if hasattr(self.form_class, "Meta") and hasattr(self.form_class.Meta, "model"):
            factory = modelformset_factory(
                self.form_class.Meta.model,
                form=self.form_class,
                **self.get_factory_kwargs(),
            )
        else:
            factory = formset_factory(self.form_class, **self.get_factory_kwargs())

        formset = factory(**self.get_formset_kwargs())

        # This sets up the initial forms, not the (same) initial data for each (new) form
        formset.initial = self.get_initial()

        # Remove form tag if using crispy forms
        for form in formset:
            if getattr(form, "helper", None):
                form.helper.form_tag = False

        return formset

    def get_context_data(self, **kwargs: Any):
        context = {}
        context["formset"] = self.get_formset()
        return context

    def formset_invalid(self):
        return render(self.request, self.template_name, self.get_context_data())

    def formset_valid(self):
        response = HTMXResponse("Formset saved successfully", tag="success")
        return response

    def get(self, request, **kwargs):
        self.request = request
        self.kwargs = kwargs

        return render(request, self.template_name, self.get_context_data())

    def post(self, request, **kwargs):
        self.request = request
        self.kwargs = kwargs
        formset = self.get_formset()

        # If the "add extra form" button was pressed, add an extra form to the formset
        if request.POST.get("add-extra-form", False):
            return self._hx_add_extra_form(request, formset)

        # formset = self.get_formset()
        else:
            formset.full_clean()
            if formset.is_valid():
                formset.save()
                return self.formset_valid()
            else:
                return self.formset_invalid()

    def _hx_add_extra_form(self, request, formset):
        """
        Creates a new form and adds it to the formset.
        Also updates the formset's total form count to reflect the addition.
        Returns the updated formset to be replaced in the DOM.
        """

        # Create a new form and add it to the formset
        # omit the form tag if using crispy forms
        form = formset.empty_form
        if getattr(form, "helper", None):
            form.helper.form_tag = False

        # add prefix to the form
        form.prefix = formset.add_prefix(formset.total_form_count())

        management_form = ManagementForm(
            auto_id=formset.auto_id,
            prefix=formset.prefix,
            initial={
                "TOTAL_FORMS": formset.total_form_count() + 1,
                "INITIAL_FORMS": formset.initial_form_count(),
                "MIN_NUM_FORMS": formset.min_num,
                "MAX_NUM_FORMS": formset.max_num,
            },
            renderer=formset.renderer,
        )

        response = render(
            request,
            self.template_name_form,
            {
                "form": form,
                "formset_prefix": formset.prefix,
                "management_form": management_form,
            },
        )
        response["HX-Retarget"] = f"#{formset.prefix}-formset-forms"
        response["HX-Reswap"] = "beforeend"
        return response


class HXCeleryTaskStatusView(SingleObjectMixin, View):
    """
    View to check the status of a Celery task and return an appropriate response.
    """

    model = TaskResult
    template_name = "htmx/celery_task_status.html"
    slug_url_kwarg = "task_id"
    success_url = None  # URL to redirect to on success, if any

    def get(self, request, *args, **kwargs):
        self.object: TaskResult = self.get_object()
        return self.get_response(request, *args, **kwargs)

    def get_slug_field(self):
        return "task_id"

    def get_response(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        response = render(request, self.template_name, context)

        if context["task"].status in ("SUCCESS", "FAILURE"):
            response["HX-Trigger"] = "task-completed"
            if success_url := self.get_success_url():
                response["HX-Redirect"] = success_url

        return response

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["task"] = self.object
        context["task_result"] = json.loads(self.object.result or "{}")

        context["refresh_interval"] = 0
        match self.object.status:
            case "PENDING":
                context["message"] = "Task is still pending..."
                context["bg_color"] = "warning"
            case "STARTED":
                context["message"] = "Task has started..."
            case "SUCCESS":
                context["message"] = "Task completed successfully."
                context["task_progress_percent"] = 100
                context["bg_color"] = "success"
            case "FAILURE":
                context["message"] = "Task failed."
                context["task_progress_percent"] = 100
                context["bg_color"] = "danger"
            case "PROGRESS":
                context["message"] = "Task in progress."
                context["refresh_interval"] = 2
                context["bg_color"] = "primary"
                context["task_progress_percent"] = (
                    context["task_result"].get("progress", 0) * 100
                )

            case _:
                context["message"] = f"Task status: {self.object.status}"
        return context

    def get_success_url(self):
        return self.success_url
