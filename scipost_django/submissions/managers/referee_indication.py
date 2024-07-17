__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models


class RefereeIndicationQuerySet(models.QuerySet):
    def suggested(self):
        return self.filter(indication=self.model.INDICATION_SUGGEST)

    def advised_against(self):
        return self.filter(indication=self.model.INDICATION_AGAINST)

    def for_submission(self, submission):
        return self.filter(submission=submission)

    def by_profile(self, profile):
        return self.filter(indicated_by=profile)

    def by_submission_authors(self, submission):
        return self.filter(
            submission=submission, indicated_by__in=submission.authors.all()
        )

    def visible_by(self, profile):
        """
        Return all referee indications that are visible to a given profile.
        For performance reasons, it assumes that results are already filtered by submission.
        - If edadmin, return all indications
        - If EIC, return all indications of the submission
        - If author, return all indications of all authors of the submission
        - Else, return self-authored indications
        """

        # Guard against empty querysets
        if not self.exists():
            return self.none()

        # Guard against querysets that are not filtered by submission
        submission = self.first().submission
        if self.values("submission").distinct().count() != 1:
            raise ValueError("Queryset must be filtered by submission")

        contributor = getattr(profile, "contributor", None)
        if contributor is not None:
            if contributor.is_ed_admin or submission.editor_in_chief == contributor:
                return self
            elif contributor in submission.authors.all():
                return self.by_submission_authors(submission)

        return self.filter(indicated_by=profile)
