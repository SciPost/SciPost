__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import serializers

from ..models import Organization

from journals.api.serializers import OrgPubFractionSerializer
from journals.models import Journal, OrgPubFraction


class OrganizationSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Organization
        fields = [
            'name', 'name_original', 'acronym', 'country'
        ]
        read_only_fields = [
            'name', 'name_original', 'acronym', 'country'
        ]


class OrganizationBalanceSerializer(serializers.BaseSerializer):
    def to_representation(self, instance):
        return instance.get_balance_info()

        # pubfractions = OrgPubFraction.objects.filter(organization=instance)
        # pubyears = range(int(timezone.now().strftime('%Y')), 2015, -1)
        # rep = {}
        # cumulative_balance = 0
        # for year in pubyears:
        #     rep[str(year)] = {}
        #     summed_expenditure = 0
        #     rep[str(year)]['expenditures'] = {}
        #     pfy = pubfractions.filter(publication__publication_date__year=year)
        #     contribution = instance.total_subsidies_in_year(year)
        #     rep[str(year)]['contribution'] = contribution
        #     journal_labels = set([f.publication.get_journal().doi_label for f in pfy.all()])
        #     for journal_label in journal_labels:
        #         sumpf = pfy.filter(
        #             publication__doi_label__istartswith=journal_label + '.'
        #         ).aggregate(Sum('fraction'))['fraction__sum']
        #         costperpaper = get_object_or_404(Journal,
        #             doi_label=journal_label).cost_per_publication(year)
        #         expenditure = int(costperpaper* sumpf)
        #         if sumpf > 0:
        #             rep[str(year)]['expenditures'][journal_label] = {
        #                 'pubfractions': sumpf,
        #                 'costperpaper': costperpaper,
        #                 'expenditure': expenditure,
        #             }
        #         summed_expenditure += expenditure
        #     rep[str(year)]['expenditures']['total'] = summed_expenditure
        #     rep[str(year)]['balance'] = contribution - summed_expenditure
        #     cumulative_balance += contribution - summed_expenditure
        # rep['cumulative'] = cumulative_balance
        # return rep
