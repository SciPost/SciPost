__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms
from django.db.models import Count, Max, Prefetch, Q

from ontology.models import Specialty
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div
from crispy_bootstrap5.bootstrap5 import FloatingField

from scipost.models import UnavailabilityPeriod
from submissions.models import Submission


class EdAdminFellowshipSearchForm(forms.Form):
    """Filter a Fellowship queryset in the edadmin monitor."""

    specialty = forms.ModelChoiceField(
        queryset=Specialty.objects.all(),
        label="Specialty",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.college = kwargs.pop("college")
        super().__init__(*args, **kwargs)
        self.fields["specialty"].queryset = self.college.specialties
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(FloatingField("specialty"), css_class="col-lg-6"),
                css_class="row",
            ),
        )

    def search_results(self):
        fellowships = self.college.fellowships.active().regular_or_senior()
        if hasattr(self, "cleaned_data") and self.cleaned_data.get("specialty"):
            fellowships = fellowships.filter(
                contributor__profile__specialties__in=[
                    self.cleaned_data.get("specialty"),
                ]
            )
        # prepare some useful prefetches
        current_unavailability_periods = UnavailabilityPeriod.objects.today()
        prefetch_current_unavailability_periods = Prefetch(
            "contributor__unavailability_periods",
            queryset=current_unavailability_periods,
            to_attr="current_unavailability_periods",
        )
        prefetch_EIC_in_stage_in_refereeing = Prefetch(
            "contributor__EIC",
            queryset=Submission.objects.in_stage_in_refereeing(),
            to_attr="EIC_in_stage_in_refereeing",
        )
        return fellowships.prefetch_related(
            "contributor__user",
            "contributor__profile__specialties",
            prefetch_current_unavailability_periods,
            prefetch_EIC_in_stage_in_refereeing,
            "qualification_set",
        ).annotate(
            nr_visible=Count(
                "pool",
                filter=Q(pool__status=Submission.SEEKING_ASSIGNMENT),
                distinct=True,
            ),
            nr_appraised=Count(
                "qualification",
                filter=Q(pool__status=Submission.SEEKING_ASSIGNMENT),
                distinct=True,
            ),
            latest_appraisal_datetime=Max(
                "qualification__datetime",
                filter=Q(status=Submission.SEEKING_ASSIGNMENT),
            ),
        )
