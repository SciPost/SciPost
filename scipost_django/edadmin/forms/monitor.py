__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms
from django.db.models import Count, Max, OuterRef, Prefetch, Subquery
from django.db.models.functions import Coalesce

from ontology.models import Specialty
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div
from crispy_bootstrap5.bootstrap5 import FloatingField

from scipost.models import UnavailabilityPeriod
from submissions.models import Submission
from submissions.models.qualification import Qualification


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

        in_pool_seeking_assignment = Submission.objects.filter(
            status=Submission.SEEKING_ASSIGNMENT,
            fellows__id__exact=OuterRef("id"),
        )
        qualifications_by_fellow = Qualification.objects.filter(
            fellow=OuterRef("id"), submission__status=Submission.SEEKING_ASSIGNMENT
        )

        return fellowships.prefetch_related(
            "contributor__dbuser",
            "contributor__profile__specialties",
            prefetch_current_unavailability_periods,
            prefetch_EIC_in_stage_in_refereeing,
            "qualification_set",
        ).annotate(
            nr_visible=Coalesce(
                Subquery(
                    in_pool_seeking_assignment.values("fellows")
                    .annotate(nr=(Count("fellows")))
                    .values("nr")
                ),
                0,
            ),
            nr_appraised=Coalesce(
                Subquery(
                    qualifications_by_fellow.values("fellow")
                    .annotate(nr=(Count("fellow")))
                    .values("nr")
                ),
                0,
            ),
            latest_appraisal_datetime=Subquery(
                qualifications_by_fellow.values("fellow")
                .annotate(latest=Max("datetime"))
                .values("latest")
            ),
        )
