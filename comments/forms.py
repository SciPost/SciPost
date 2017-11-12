from django import forms

from .constants import COMMENT_ACTION_CHOICES, COMMENT_REFUSAL_CHOICES
from .models import Comment


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['is_cor', 'is_rem', 'is_que', 'is_ans', 'is_obj',
                  'is_rep', 'is_val', 'is_lit', 'is_sug',
                  'comment_text', 'remarks_for_editors', 'file_attachment']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['comment_text'].widget.attrs.update(
            {'placeholder': 'NOTE: only serious and meaningful Comments will be accepted.'})
        self.fields['remarks_for_editors'].widget.attrs.update(
            {'rows': 3, 'placeholder': '(these remarks will not be publicly visible)'})


class VetCommentForm(forms.Form):
    action_option = forms.ChoiceField(widget=forms.RadioSelect, choices=COMMENT_ACTION_CHOICES,
                                      required=True, label='Action')
    refusal_reason = forms.ChoiceField(choices=COMMENT_REFUSAL_CHOICES)
    email_response_field = forms.CharField(widget=forms.Textarea(),
                                           label='Justification (optional)', required=False)
