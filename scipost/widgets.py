__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.forms.widgets import CheckboxSelectMultiple


class SelectButtonWidget(CheckboxSelectMultiple):
    template_name = 'widgets/checkbox_as_btn.html'
