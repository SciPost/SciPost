__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from .models import College, Fellowship, FellowshipNomination
import datetime
from django.utils import timezone


def check_profile_eligibility_for_fellowship(profile):
    """
    Returns a list of failed eligibility criteria (if any).

    Requirements:

    - Profile has a known acad_field
    - Profile has at least one specialty
    - There is an active College in the Profile's acad_field
    - no current Fellowship exists
    - no current FellowshipNomination exists
    - no 'not elected' decision in last 2 years
    - no invitation was turned down in the last 2 years
    """
    blocks = []
    if not profile.acad_field:
        blocks.append(
            "No academic field is specified for this profile. "
            "Contact EdAdmin or techsupport."
        )
    elif not College.objects.filter(acad_field=profile.acad_field).exists():
        blocks.append(
            "There is currently no College in {profile.acad_field}. "
            "Contact EdAdmin or techsupport to get one started."
        )
    if (
        Fellowship.objects.active()
        .regular_or_senior()
        .filter(contributor__profile=profile)
        .exists()
    ):
        blocks.append("This Profile is associated to an active Fellowship.")
    latest_nomination = FellowshipNomination.objects.filter(profile=profile).first()
    if latest_nomination:
        try:
            if (
                latest_nomination.decision.fixed_on + datetime.timedelta(days=730)
            ) > timezone.now():
                if latest_nomination.decision.elected:
                    try:
                        if latest_nomination.invitation.declined:
                            blocks.append(
                                "Invitation declined less that 2 years ago. "
                                "Wait to try again."
                            )
                        else:
                            blocks.append("Already elected, invitation in process.")
                    except AttributeError:
                        blocks.append("Already elected, invitation pending.")
                blocks.append("Election failed less that 2 years ago. Must wait.")
        except AttributeError:  # no decision yet
            blocks.append(
                "This Profile is associated to an ongoing Nomination process."
            )
    return blocks if len(blocks) > 0 else None
