__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from .models import Journal


REGEX_CHOICES = '|'.join([j.doi_label for j in Journal.objects.all()])


# Regex used for URLs of specific Publications and for
# doi validation during the publication process.
PUBLICATION_DOI_REGEX = r'({})'.format(REGEX_CHOICES)
PUBLICATION_DOI_REGEX += r'(\.\w+(\.[0-9]+(\.[0-9]{3,})?)?)?'
PUBLICATION_DOI_VALIDATION_REGEX = PUBLICATION_DOI_REGEX
DOI_DISPATCH_REGEX = r'(?P<journal_tag>{})'.format(REGEX_CHOICES)
DOI_DISPATCH_REGEX += r'(\.(?P<part_1>\w+)(\.(?P<part_2>[0-9]+)(\.(?P<part_3>[0-9]{3,}))?)?)?'

DOI_ISSUE_REGEX = r'(?P<doi_label>({})\.\w+(\.[0-9]+)?)'.format(REGEX_CHOICES)
