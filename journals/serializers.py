__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import serializers

from .models import Publication


class StringListField(serializers.ListField):
    child = serializers.CharField()


class PublicationSerializerForGoogleScholar(serializers.BaseSerializer):
    citation_title = serializers.CharField(max_length=512)
    citation_authors = StringListField()
    citation_doi = serializers.CharField(max_length=256)
    citation_publication_date = serializers.DateField()
    citation_journal_title = serializers.CharField(max_length=128)
    citation_issn = serializers.CharField(max_length=16)
    citation_volume = serializers.IntegerField()
    citation_issue = serializers.IntegerField()
    citation_firstpage = serializers.CharField(max_length=16)
    citation_pdf_url = serializers.URLField()
    dc_identifier = serializers.CharField(max_length=64)

    def to_representation(self, instance):
        """
        Convert to a Google Scholar-appropriate JSON format.
        """
        authors = []
        for author in instance.authors.all():
            if author.contributor:
                authors.append('%s, %s' % (author.contributor.user.last_name,
                                           author.contributor.user.first_name))
            elif author.unregistered_author:
                authors.append('%s, %s' % (author.unregistered_author.last_name,
                                           author.unregistered_author.first_name))
        rep = {
            'citation_title': instance.title,
            'citation_authors': authors,
            'citation_doi': instance.doi_string,
            'citation_publication_date': instance.publication_date.strftime('%Y/%m/%d'),
            'citation_journal_title': str(instance.get_journal()),
            'citation_issn': instance.get_journal().issn,
        }
        if instance.in_issue:
            rep['citation_volume'] = instance.in_issue.in_volume.number
            rep['citation_issue'] = instance.in_issue.number
        rep['citation_firstpage'] = instance.get_paper_nr()
        rep['citation_pdf_url'] = 'https://scipost.org%s/pdf' % instance.get_absolute_url()
        rep['dc_identifier'] = instance.doi_string
        return rep
