__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import abc
from django.http import HttpRequest, HttpResponse
from django.views.generic.edit import ModelFormMixin

from ethics.forms import GenAIDisclosureForm
from ethics.models import GenAIDisclosure
from scipost.models import Contributor

from typing import Any


class GenAIFormViewInjectorMixin(ModelFormMixin):
    """
    Mixin to inject the GenAI disclosure form into existing form views.
    """

    def get_gen_ai_disclosure_contributor(self) -> Contributor | None:
        """
        Returns the Contributor instance for the current user making the request.
        """
        return Contributor.objects.get(user=self.request.user)

    def post(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        try:
            self.object = self.get_object()  # Required to set by SingleObjectMixin
        except AttributeError:
            self.object = None

        self.request = request

        form = self.get_form()
        gen_ai_form = self.get_gen_ai_disclosure_form()

        # Override superclass `post` to check for disclosure form validity
        if form.is_valid() and (gen_ai_form.is_valid() if gen_ai_form else True):
            response = self.form_valid(form)
            if gen_ai_form:
                self.gen_ai_form_valid(gen_ai_form)
            return response
        else:
            return self.form_invalid(form)

    def gen_ai_form_valid(self, form: GenAIDisclosureForm) -> None:
        author = self.get_gen_ai_disclosure_contributor()
        if author is None:
            raise ValueError(
                "No Contributor found to set as author for GenAI disclosure."
            )

        form.save(contributor=author, for_object=self.object)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        if gen_ai_form := self.get_gen_ai_disclosure_form():
            context["gen_ai_disclosure_form"] = gen_ai_form
        return context

    def get_gen_ai_disclosure_form(self) -> GenAIDisclosureForm | None:
        return GenAIDisclosureForm(**self.get_form_kwargs())

    @abc.abstractmethod
    def get_gen_ai_disclosure(self) -> GenAIDisclosure | None:
        return None
