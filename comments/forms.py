from django import *

from .models import *

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, Fieldset, HTML, Submit


COMMENT_ACTION_CHOICES = (
#    (0, 'modify'), 
    (1, 'accept'), 
    (2, 'refuse (give reason below)'),
    )

COMMENT_REFUSAL_CHOICES = (
    (0, '-'),
    (-1, 'unclear'),
    (-2, 'incorrect'),
    (-3, 'not useful'),
    )
comment_refusal_dict = dict(COMMENT_REFUSAL_CHOICES)


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['is_rem', 'is_que', 'is_ans', 'is_obj', 'is_rep', 'is_val', 'is_lit', 'is_sug', 'comment_text', 'remarks_for_editors']

    def __init__(self, *args, **kwargs):
        super(CommentForm, self).__init__(*args, **kwargs)
        self.fields['comment_text'].widget.attrs.update({'placeholder': 'NOTE: only serious and meaningful Comments will be accepted.'})
        self.fields['remarks_for_editors'].widget.attrs.update({'rows': 3, 'placeholder': '(these remarks will not be publicly visible)'})
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    Field('comment_text'), 
                    HTML('<p>In your comment, you can use LaTeX \$...\$ for in-text equations or \ [ ... \ ] for on-line equations.</p>'),
                    HTML('<p id="goodCommenter"><i>Be professional. Only serious and meaningful comments will be vetted through.</i></p><br/>'),
                    Field('remarks_for_editors'),
                    css_class="col-9"),
                Div(
                    Fieldset(
                        'Specify categorization(s):',
                        'is_rem', 'is_que', 'is_ans', 'is_obj', 'is_rep', 'is_val', 'is_lit', 'is_sug',
                        style="border: 0px; font-size: 90%"),
                    HTML('<br>'),
                    Div(
                        Submit('submit', 'Submit your Comment for vetting', css_class="submitComment"),
                        HTML('<p id="goodCommenter"><i>By clicking on Submit, the commenter agrees to the <a href="{% url \'scipost:terms_and_conditions\' %}">Terms and Conditions</a>.</i></p>'),
                        ),
                    css_class="col-3"),
                css_class="row"),
            )
        
                
    

class VetCommentForm(forms.Form):
    action_option = forms.ChoiceField(widget=forms.RadioSelect, choices=COMMENT_ACTION_CHOICES, required=True, label='Action')
    refusal_reason = forms.ChoiceField(choices=COMMENT_REFUSAL_CHOICES)
    email_response_field = forms.CharField(widget=forms.Textarea(), label='Justification (optional)', required=False)


