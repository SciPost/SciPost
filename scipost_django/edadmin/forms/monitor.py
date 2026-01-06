__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms
from django.db.models import QuerySet

from colleges.models.fellowship import Fellowship
from common.forms import CrispyFormMixin, SearchForm
from ontology.models import Specialty


class EdAdminFellowshipSearchForm(CrispyFormMixin, SearchForm[Fellowship]):
    model = Fellowship

    fellow = forms.CharField(
        label="Fellow name",
        required=False,
    )
    specialty = forms.ModelChoiceField(
        queryset=Specialty.objects.all(),
        label="Specialty",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.college = kwargs.pop("college")
        self.queryset = self.college.fellowships.active().regular_or_senior()
        super().__init__(*args, **kwargs)
        self.fields["specialty"].queryset = self.college.specialties

    def filter_queryset(self, queryset: QuerySet[Fellowship]) -> QuerySet[Fellowship]:
        if specialty := self.cleaned_data.get("specialty"):
            queryset = queryset.filter(contributor__profile__specialties=specialty)
        if fellow := self.cleaned_data.get("fellow"):
            queryset = queryset.filter(
                contributor__profile__full_name__icontains=fellow
            )
        return queryset
