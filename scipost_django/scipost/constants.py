__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


APPROACH_THEORETICAL = 'theoretical'
APPROACH_EXPERIMENTAL = 'experimental'
APPROACH_COMPUTATIONAL = 'computational'
APPROACH_PHENOMENOLOGICAL = 'phenomenological'
APPROACH_OBSERVATIONAL = 'observational'
APPROACH_CLINICAL = 'clinical'

SCIPOST_APPROACHES = (
    (APPROACH_THEORETICAL, 'Theoretical'),
    (APPROACH_EXPERIMENTAL, 'Experimental'),
    (APPROACH_COMPUTATIONAL, 'Computational'),
    (APPROACH_PHENOMENOLOGICAL, 'Phenomenological'),
    (APPROACH_OBSERVATIONAL, 'Observational'),
    (APPROACH_CLINICAL, 'Clinical'),
)


# Contributor types
NEWLY_REGISTERED, NORMAL_CONTRIBUTOR = 'newly_registered', 'normal'
UNVERIFIABLE_CREDENTIALS, NO_SCIENTIST = 'unverifiable', 'no_scientist'
DOUBLE_ACCOUNT, OUT_OF_ACADEMIA = 'double_account', 'out_of_academia'
BARRED, DISABLED, DECEASED = 'barred', 'disabled', 'deceased'
CONTRIBUTOR_STATUSES = (
    (NEWLY_REGISTERED, 'Newly registered'),
    (NORMAL_CONTRIBUTOR, 'Normal user'),
    (UNVERIFIABLE_CREDENTIALS, 'Unverifiable credentials'),
    (NO_SCIENTIST, 'Not a professional scientist'),
    (DOUBLE_ACCOUNT, 'Other account already exists'),
    (OUT_OF_ACADEMIA, 'Out of academia'),
    (BARRED, 'Barred from SciPost'),
    (DISABLED, 'Account disabled'),
    (DECEASED, 'Person deceased')
)

TITLE_DR = 'DR'
TITLE_CHOICES = (
    ('PR', 'Prof.'),
    ('DR', 'Dr'),
    ('MR', 'Mr'),
    ('MRS', 'Mrs'),
    ('MS', 'Ms'),
    ('MX', 'Mx'),
)

INVITATION_EDITORIAL_FELLOW = 'F'
INVITATION_CONTRIBUTOR = 'C'
INVITATION_REFEREEING = 'R'
INVITATION_CITED_SUBMISSION = 'ci'
INVITATION_CITED_PUBLICATION = 'cp'
INVITATION_TYPE = (
    (INVITATION_EDITORIAL_FELLOW, 'Editorial Fellow'),
    (INVITATION_CONTRIBUTOR, 'Contributor'),
    (INVITATION_REFEREEING, 'Refereeing'),
    (INVITATION_CITED_SUBMISSION, 'cited in submission'),
    (INVITATION_CITED_PUBLICATION, 'cited in publication'),
)

INVITATION_FORMAL = 'F'
INVITATION_PERSONAL = 'P'
INVITATION_STYLE = (
    (INVITATION_FORMAL, 'formal'),
    (INVITATION_PERSONAL, 'personal'),
)

AUTHORSHIP_CLAIM_ACCEPTED = 1
AUTHORSHIP_CLAIM_PENDING = 0
AUTHORSHIP_CLAIM_REJECTED = -1
AUTHORSHIP_CLAIM_STATUS = (
    (AUTHORSHIP_CLAIM_ACCEPTED, 'accepted'),
    (AUTHORSHIP_CLAIM_PENDING, 'not yet vetted (pending)'),
    (AUTHORSHIP_CLAIM_REJECTED, 'rejected'),
)

SCIPOST_FROM_ADDRESSES = (
    ('Admin', 'SciPost Admin <admin@scipost.org>'),
    ('J.-S. Caux', 'J.-S. Caux <jscaux@scipost.org>'),
    ('J. van Wezel', 'J. van Wezel <vanwezel@scipost.org>'),
)
SciPost_from_addresses_dict = dict(SCIPOST_FROM_ADDRESSES)
