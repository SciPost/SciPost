from django import *

from .models import *

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

AUTHOR_REPLY_ACTION_CHOICES = (
#    (0, 'modify'), 
    (1, 'accept'), 
    (2, 'refuse (give reason below)'),
    )

AUTHOR_REPLY_REFUSAL_CHOICES = (
    (0, '-'),
    (-1, 'unclear'),
    (-2, 'incorrect'),
    (-3, 'not useful'),
    (-4, 'not from an author'),
    )


#class CommentForm(forms.Form):
##    category = forms.MultipleChoiceField(choices=COMMENT_CATEGORIES, widget=forms.CheckboxSelectMultiple(), label='Please categorize your comment (multiple choices allowed):')
#    is_rem = forms.BooleanField(required=False, label='remark')
#    is_que = forms.BooleanField(required=False, label='question')
#    is_ans = forms.BooleanField(required=False, label='answer to question')
#    is_obj = forms.BooleanField(required=False, label='objection')
#    is_rep = forms.BooleanField(required=False, label='reply to objection')
#    is_val = forms.BooleanField(required=False, label='validation or rederivation')
#    is_lit = forms.BooleanField(required=False, label='pointer to related literature')
#    is_sug = forms.BooleanField(required=False, label='suggestions for further work')
#    comment_text = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols':80}), label='', required=True) # need TextField but doesn't exist
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['is_rem', 'is_que', 'is_ans', 'is_obj', 'is_rep', 'is_val', 'is_lit', 'is_sug', 'comment_text', 'anonymous']

    def __init__(self, *args, **kwargs):
        super(CommentForm, self).__init__(*args, **kwargs)
        self.fields['comment_text'].widget.attrs.update({'placeholder': 'NOTE: only serious and meaningful Comments will be accepted.'})

class VetCommentForm(forms.Form):
    action_option = forms.ChoiceField(widget=forms.RadioSelect, choices=COMMENT_ACTION_CHOICES, required=True, label='Action')
    refusal_reason = forms.ChoiceField(choices=COMMENT_REFUSAL_CHOICES)
    email_response_field = forms.CharField(widget=forms.Textarea(), label='Justification (optional)', required=False)


#class AuthorReplyForm(forms.Form):
#    reply_text = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols':80}), label='', required=True) 
## need TextField but doesn't exist
class AuthorReplyForm(forms.ModelForm):
    class Meta:
        model = AuthorReply
        fields = ['reply_text']

class VetAuthorReplyForm(forms.Form):
    action_option = forms.ChoiceField(widget=forms.RadioSelect, choices=AUTHOR_REPLY_ACTION_CHOICES, required=True, label='Action')
    refusal_reason = forms.ChoiceField(choices=AUTHOR_REPLY_REFUSAL_CHOICES)
    email_response_field = forms.CharField(widget=forms.Textarea(), label='Justification (optional)', required=False)
