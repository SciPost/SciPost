__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django import forms

from proceedings.models import Proceedings
from submissions.models import Submission
from scipost.models import Contributor

from .models import Fellowship, ProspectiveFellow, ProspectiveFellowEvent


class AddFellowshipForm(forms.ModelForm):
    class Meta:
        model = Fellowship
        fields = (
            'guest',
            'contributor',
            'start_date',
            'until_date',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['contributor'].queryset = Contributor.objects.active()
        self.fields['contributor'].label = "Fellow"

    def clean(self):
        start = self.cleaned_data.get('start_date')
        until = self.cleaned_data.get('until_date')
        if start and until:
            if until <= start:
                self.add_error('until_date', 'The given dates are not in chronological order.')


class FellowshipForm(forms.ModelForm):
    class Meta:
        model = Fellowship
        fields = (
            'guest',
            'start_date',
            'until_date',
        )

    def clean(self):
        start = self.cleaned_data.get('start_date')
        until = self.cleaned_data.get('until_date')
        if start and until:
            if until <= start:
                self.add_error('until_date', 'The given dates are not in chronological order.')


class FellowshipTerminateForm(forms.ModelForm):
    class Meta:
        model = Fellowship
        fields = []

    def save(self):
        today = datetime.date.today()
        fellowship = self.instance
        if fellowship.until_date > today:
            fellowship.until_date = today
        return fellowship.save()


class FellowshipRemoveSubmissionForm(forms.ModelForm):
    """
    Use this form in admin-accessible views only! It could possibly reveal the
    identity of the Editor-in-charge!
    """
    class Meta:
        model = Fellowship
        fields = []

    def __init__(self, *args, **kwargs):
        self.submission = kwargs.pop('submission')
        super().__init__(*args, **kwargs)

    def clean(self):
        if self.submission.editor_in_charge == self.instance.contributor:
            self.add_error(None, ('Submission cannot be removed as the Fellow is'
                                  ' Editor-in-charge of this Submission.'))

    def save(self):
        fellowship = self.instance
        fellowship.pool.remove(self.submission)
        return fellowship


class FellowVotingRemoveSubmissionForm(forms.ModelForm):
    """
    Use this form in admin-accessible views only! It could possibly reveal the
    identity of the Editor-in-charge!
    """
    class Meta:
        model = Fellowship
        fields = []

    def __init__(self, *args, **kwargs):
        self.submission = kwargs.pop('submission')
        super().__init__(*args, **kwargs)

    def clean(self):
        if self.submission.editor_in_charge == self.instance.contributor:
            self.add_error(None, ('Submission cannot be removed as the Fellow is'
                                  ' Editor-in-charge of this Submission.'))

    def save(self):
        fellowship = self.instance
        fellowship.voting_pool.remove(self.submission)
        return fellowship


class FellowshipAddSubmissionForm(forms.ModelForm):
    submission = forms.ModelChoiceField(queryset=None, to_field_name='arxiv_identifier_w_vn_nr',
                                        empty_label="Please choose the Submission to add to the pool")

    class Meta:
        model = Fellowship
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pool = self.instance.pool.values_list('id', flat=True)
        self.fields['submission'].queryset = Submission.objects.exclude(id__in=pool)

    def save(self):
        submission = self.cleaned_data['submission']
        fellowship = self.instance
        fellowship.pool.add(submission)
        return fellowship


class SubmissionAddFellowshipForm(forms.ModelForm):
    fellowship = forms.ModelChoiceField(queryset=None, to_field_name='id',
                                        empty_label="Please choose the Fellow to add to the Pool")

    class Meta:
        model = Submission
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pool = self.instance.fellows.values_list('id', flat=True)
        self.fields['fellowship'].queryset = Fellowship.objects.active().exclude(id__in=pool)

    def save(self):
        fellowship = self.cleaned_data['fellowship']
        submission = self.instance
        submission.fellows.add(fellowship)
        return submission


class SubmissionAddVotingFellowForm(forms.ModelForm):
    fellowship = forms.ModelChoiceField(
        queryset=None, to_field_name='id',
        empty_label="Please choose the Fellow to add to the Submission's Voting Fellows")

    class Meta:
        model = Submission
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pool = self.instance.voting_fellows.values_list('id', flat=True)
        self.fields['fellowship'].queryset = Fellowship.objects.active().exclude(id__in=pool)

    def save(self):
        fellowship = self.cleaned_data['fellowship']
        submission = self.instance
        submission.fellows.add(fellowship)
        submission.voting_fellows.add(fellowship)
        return submission


class FellowshipRemoveProceedingsForm(forms.ModelForm):
    """
    Use this form in admin-accessible views only! It could possibly reveal the
    identity of the Editor-in-charge!
    """
    class Meta:
        model = Fellowship
        fields = []

    def __init__(self, *args, **kwargs):
        self.proceedings = kwargs.pop('proceedings')
        super().__init__(*args, **kwargs)

    def clean(self):
        if self.proceedings.lead_fellow == self.instance:
            self.add_error(None, 'Fellowship cannot be removed as it is assigned as lead fellow.')

    def save(self):
        fellowship = self.instance
        self.proceedings.fellowships.remove(fellowship)
        return fellowship


class FellowshipAddProceedingsForm(forms.ModelForm):
    proceedings = forms.ModelChoiceField(queryset=None, to_field_name='id',
                                         empty_label="Please choose the Proceedings to add to the Pool")

    class Meta:
        model = Fellowship
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        proceedings = self.instance.proceedings.values_list('id', flat=True)
        self.fields['proceedings'].queryset = Proceedings.objects.exclude(id__in=proceedings)

    def save(self):
        proceedings = self.cleaned_data['proceedings']
        fellowship = self.instance
        proceedings.fellowships.add(fellowship)
        return fellowship


class ProspectiveFellowCreateForm(forms.ModelForm):

    class Meta:
        model = ProspectiveFellow
        fields = ['title', 'first_name', 'last_name', 'email',
                  'discipline', 'expertises', 'webpage', 'status', 'contributor']


class ProspectiveFellowEventCreateForm(forms.ModelForm):

    class Meta:
        model = ProspectiveFellowEvent
        fields = ['event', 'comments']
