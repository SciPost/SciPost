from django import forms

from .constants import COMMENT_ACTION_CHOICES, COMMENT_REFUSAL_CHOICES
from .models import Comment

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, Fieldset, HTML, Submit


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['is_cor', 'is_rem', 'is_que', 'is_ans', 'is_obj',
                  'is_rep', 'is_val', 'is_lit', 'is_sug',
                  'comment_text', 'remarks_for_editors', 'file_attachment']

    def __init__(self, *args, **kwargs):
        super(CommentForm, self).__init__(*args, **kwargs)
        self.fields['comment_text'].widget.attrs.update(
            {'placeholder': 'NOTE: only serious and meaningful Comments will be accepted.'})
        self.fields['remarks_for_editors'].widget.attrs.update(
            {'rows': 3, 'placeholder': '(these remarks will not be publicly visible)'})
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    Field('comment_text'),
                    HTML('<p>In your comment, you can use LaTeX \$...\$ for in-text '
                         'equations or \ [ ... \ ] for on-line equations.</p>'),
                    HTML('<p id="goodCommenter"><i>Be professional. Only serious and '
                         'meaningful comments will be vetted through.</i></p><br/>'),
                    Field('remarks_for_editors'),
                    css_class="col-md-9"),
                Div(
                    Fieldset(
                        'Specify categorization(s):',
                        'is_cor', 'is_rem', 'is_que', 'is_ans', 'is_obj',
                        'is_rep', 'is_val', 'is_lit', 'is_sug',
                        style="border: 0px; font-size: 90%"),
                    HTML('<br>'),
                    Div(
                        Submit('submit', 'Submit your Comment for vetting',
                               css_class="submitButton"),
                        HTML('<p id="goodCommenter"><i>By clicking on Submit, you agree with the '
                             '<a href="{% url \'scipost:terms_and_conditions\' %}">'
                             'Terms and Conditions</a>.</i></p>'),
                        ),
                    css_class="col-md-3"),
                css_class="row"),
            )


class VetCommentForm(forms.Form):
    action_option = forms.ChoiceField(widget=forms.RadioSelect, choices=COMMENT_ACTION_CHOICES,
                                      required=True, label='Action')
    refusal_reason = forms.ChoiceField(choices=COMMENT_REFUSAL_CHOICES)
    email_response_field = forms.CharField(widget=forms.Textarea(),
                                           label='Justification (optional)', required=False)
