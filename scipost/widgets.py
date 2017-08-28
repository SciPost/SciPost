from django.forms.widgets import CheckboxSelectMultiple


class SelectButtonWidget(CheckboxSelectMultiple):
    template_name = 'widgets/checkbox_as_btn.html'
