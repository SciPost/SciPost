__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.forms.widgets import Textarea

from .utils import process_markup


class TextareaWithPreview(Textarea):
    template_name = "markup/forms/widgets/textarea_with_preview.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["value_processed"] = process_markup(
            context["widget"]["value"],
            include_errors=True,
        )
        return context
