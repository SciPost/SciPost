__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf import settings

import ithenticate_python_api.core as TCA

from journals.models.journal import Journal
from profiles.models import Profile

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from submissions.models.submission import Submission


class SciPostiThenticateService(TCA.iThenticateService):
    def __init__(self):
        super().__init__(
            tenant=settings.TCA_TENANT,
            api_key=settings.TCA_API_KEY,
            integration_name=settings.TCA_INTEGRATION_NAME,
            integration_version=settings.TCA_INTEGRATION_VERSION,
        )

    @classmethod
    def tca_user_from_profile(cls, profile: Profile) -> TCA.User:
        """Create an iThenticate user from a SciPost Profile."""
        return TCA.User(
            id=str(profile.id),
            given_name=profile.first_name,
            family_name=profile.last_name,
            email=profile.email or "unknown@example.com",
        )

    def tca_group_from_journal(self, journal: Journal) -> TCA.Group:
        """Create an iThenticate group from a SciPost Journal,
        with the group context being the journal's academic field."""
        acad_field_context = TCA.GroupContext(
            name=journal.college.acad_field.name,
            owners=[
                self.tca_user_from_profile(profile)
                for profile in Profile.objects.filter(
                    contributor__dbuser__groups__name="Editorial Administration"
                )
            ],
        )

        group = TCA.Group(
            id=str(journal.id),
            name=journal.name,
            type=TCA.GroupType.FOLDER,
            context=acad_field_context,
        )
        group.set_client(self.client)

        return group

    def tca_submission_from_submission(
        self, submission: "Submission"
    ) -> TCA.Submission:
        """Create an iThenticate submission from a SciPost Submission."""
        journal_group = self.tca_group_from_journal(submission.submitted_to)
        acad_field_context = journal_group.context

        tca_sub = TCA.Submission(
            title=submission.title,
            authors=[
                self.tca_user_from_profile(profile)
                for author in submission.author_profiles.all()
                if (profile := author.profile)
            ],
            group=journal_group,
            group_context=acad_field_context,
            custom_metadata={
                "preprint_identifier": submission.preprint.identifier_w_vn_nr
            },
        )
        tca_sub.set_client(self.client)

        return tca_sub