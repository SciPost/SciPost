__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import serializers

from ..models import Publication


class StringListField(serializers.ListField):
    child = serializers.CharField()


class PublicationSerializer(serializers.BaseSerializer):
    title = serializers.CharField(max_length=512)
    authors = StringListField()
    doi = serializers.CharField(max_length=256)
    publication_date = serializers.DateField()
    journal_title = serializers.CharField(max_length=128)
    issn = serializers.CharField(max_length=16)
    volume = serializers.IntegerField()
    issue = serializers.IntegerField()
    pdf_url = serializers.URLField()

    def to_representation(self, instance):
        """
        Convert publication information to a JSON format.
        """
        authors = []
        for author in instance.authors.all():
            authors.append('%s, %s' % (author.profile.last_name,
                                       author.profile.first_name))
        rep = {
            'title': instance.title,
            'authors': authors,
            'doi': instance.doi_string,
            'publication_date': instance.publication_date.strftime('%Y/%m/%d'),
            'journal_title': str(instance.get_journal()),
            'issn': instance.get_journal().issn,
        }
        if instance.in_issue:
            if instance.in_issue.in_volume:
                rep['volume'] = instance.in_issue.in_volume.number
            rep['issue'] = instance.in_issue.number
        rep['pdf_url'] = 'https://scipost.org%s/pdf' % instance.get_absolute_url()
        return rep
