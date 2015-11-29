from django import forms

from .models import *

REGISTRATION_REFUSAL_CHOICES = (
    (0, '-'),
    (-1, 'not a professional scientist (>= PhD student)'),
    (-2, 'another account already exists for this person'),
    (-3, 'barred from SciPost (abusive behaviour)'),
    )

COMMENTARY_ACTION_CHOICES = (
    (0, 'modify'), 
    (1, 'accept'), 
    (2, 'refuse (give reason below)'),
    )

COMMENTARY_REFUSAL_CHOICES = (
    (0, '-'),
    (-1, 'a commentary on this paper already exists'),
    (-2, 'this paper cannot be traced'),
    )

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

REPORT_ACTION_CHOICES = (
#    (0, 'modify'), 
    (1, 'accept'), 
    (2, 'refuse (give reason below)'),
    )

REPORT_REFUSAL_CHOICES = (
    (0, '-'),
    (-1, 'unclear'),
    (-2, 'incorrect'),
    (-3, 'not useful'),
    (-4, 'not academic in style'),
    )



class RegistrationForm(forms.Form):
    title = forms.ChoiceField(choices=TITLE_CHOICES)
    first_name = forms.CharField(label='First name', max_length=100)
    last_name = forms.CharField(label='Last name', max_length=100)
    email = forms.EmailField(label='email')
    orcid_id = forms.CharField(label="ORCID id", max_length=20, required=False)
    affiliation = forms.CharField(label='Affiliation', max_length=300)
    address = forms.CharField(label='Address', max_length=1000, required=False)
    personalwebpage = forms.URLField(label='Personal web page', required=False)
    username = forms.CharField(label='username', max_length=100)
    password = forms.CharField(label='password', widget=forms.PasswordInput())

class VetRegistrationForm(forms.Form):
    promote_to_rank_1 = forms.BooleanField(required=False)
    refusal_reason = forms.ChoiceField(choices=REGISTRATION_REFUSAL_CHOICES, required=False)
    email_response_field = forms.CharField(widget=forms.Textarea(), label='Justification (optional)', required=False)

class AuthenticationForm(forms.Form):
    username = forms.CharField(label='username', max_length=100)
    password = forms.CharField(label='password', widget=forms.PasswordInput())




class RequestCommentaryForm(forms.Form):
    type = forms.ChoiceField(choices=COMMENTARY_TYPES)
    pub_title = forms.CharField(max_length=300, label="Title")
    author_list = forms.CharField(max_length=1000)
    pub_date = forms.DateField(label="Publication date (YYYY-MM-DD)")
    arxiv_link = forms.URLField(label='arXiv link (including version nr)', required=False)
    pub_DOI_link = forms.URLField(label='DOI link to the published version', required=False)
    pub_abstract = forms.CharField(widget=forms.Textarea, label="Abstract") # need TextField but doesn't exist
    
class VetCommentaryForm(forms.Form):
    action_option = forms.ChoiceField(widget=forms.RadioSelect, choices=COMMENTARY_ACTION_CHOICES, required=True, label='Action')
    refusal_reason = forms.ChoiceField(choices=COMMENTARY_REFUSAL_CHOICES, required=False)
    email_response_field = forms.CharField(widget=forms.Textarea(attrs={'rows': 5, 'cols': 40}), label='Justification (optional)', required=False)

class CommentarySearchForm(forms.Form):
    pub_author = forms.CharField(max_length=100, required=False, label="Author(s)")
    pub_title_keyword = forms.CharField(max_length=100, label="Title", required=False)
    pub_abstract_keyword = forms.CharField(max_length=1000, required=False, label="Abstract")

class CommentaryRatingForm(forms.Form):
    clarity = forms.ChoiceField(RATING_CHOICES)
    correctness = forms.ChoiceField(RATING_CHOICES)
    usefulness = forms.ChoiceField(RATING_CHOICES)



class CommentForm(forms.Form):
    comment_text = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols':80}), label='', required=True) # need TextField but doesn't exist

class VetCommentForm(forms.Form):
    action_option = forms.ChoiceField(widget=forms.RadioSelect, choices=COMMENT_ACTION_CHOICES, required=True, label='Action')
    refusal_reason = forms.ChoiceField(choices=COMMENT_REFUSAL_CHOICES)
    email_response_field = forms.CharField(widget=forms.Textarea(), label='Justification (optional)', required=False)

class CommentRatingForm(forms.Form):
    clarity = forms.ChoiceField(RATING_CHOICES)
    correctness = forms.ChoiceField(RATING_CHOICES)
    usefulness = forms.ChoiceField(RATING_CHOICES)

class AuthorReplyForm(forms.Form):
    reply_text = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols':80}), label='', required=True) 
# need TextField but doesn't exist

class VetAuthorReplyForm(forms.Form):
    action_option = forms.ChoiceField(widget=forms.RadioSelect, choices=AUTHOR_REPLY_ACTION_CHOICES, required=True, label='Action')
    refusal_reason = forms.ChoiceField(choices=AUTHOR_REPLY_REFUSAL_CHOICES)
    email_response_field = forms.CharField(widget=forms.Textarea(), label='Justification (optional)', required=False)

class AuthorReplyRatingForm(forms.Form):
    clarity = forms.ChoiceField(RATING_CHOICES)
    correctness = forms.ChoiceField(RATING_CHOICES)
    usefulness = forms.ChoiceField(RATING_CHOICES)



class SubmissionForm(forms.Form):
    submitted_to_journal = forms.ChoiceField(choices=SCIPOST_JOURNALS_SUBMIT, required=True, label='SciPost Journal to submit to:')
    domain = forms.ChoiceField(choices=SCIPOST_JOURNALS_DOMAINS)
    specialization = forms.ChoiceField(choices=SCIPOST_JOURNALS_SPECIALIZATIONS)
    title = forms.CharField(max_length=300, required=True, label='Title')
    author_list = forms.CharField(max_length=1000, required=True)
    abstract = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols':60}), label='Abstract', required=True) # need TextField but doesn't exist
    arxiv_link = forms.URLField(label='arXiv link (including version nr)', required=True)

class ProcessSubmissionForm(forms.Form):
    editor_in_charge = forms.ModelChoiceField(queryset=Contributor.objects.filter(rank__gte=3))

class SubmissionSearchForm(forms.Form):
    author = forms.CharField(max_length=100, required=False, label="Author(s)")
    title_keyword = forms.CharField(max_length=100, label="Title", required=False)
    abstract_keyword = forms.CharField(max_length=1000, required=False, label="Abstract")

class SubmissionRatingForm(forms.Form):
    clarity = forms.ChoiceField(RATING_CHOICES)
    correctness = forms.ChoiceField(RATING_CHOICES)
    usefulness = forms.ChoiceField(RATING_CHOICES)



class ReportForm(forms.Form):
    qualification = forms.ChoiceField(RATING_CHOICES, label='Your degree of qualification in assessing this Submission')
    strengths = forms.CharField(widget=forms.Textarea(), required=False)
    weaknesses = forms.CharField(widget=forms.Textarea(), required=False)
    report = forms.CharField(widget=forms.Textarea(), required=False)
    requested_changes = forms.CharField(widget=forms.Textarea(), required=False)
    recommendation = forms.ChoiceField(choices=REPORT_REC)

class VetReportForm(forms.Form):
    action_option = forms.ChoiceField(widget=forms.RadioSelect, choices=REPORT_ACTION_CHOICES, required=True, label='Action')
    refusal_reason = forms.ChoiceField(choices=REPORT_REFUSAL_CHOICES)
    email_response_field = forms.CharField(widget=forms.Textarea(), label='Justification (optional)', required=False)

class ReportRatingForm(forms.Form):
    clarity = forms.ChoiceField(RATING_CHOICES)
    correctness = forms.ChoiceField(RATING_CHOICES)
    usefulness = forms.ChoiceField(RATING_CHOICES)
