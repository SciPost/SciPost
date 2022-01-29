__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from .models import Fellowship, FellowshipNomination


def check_profile_eligibility_for_fellowship(profile):
    """
    Returns a list of failed eligibility criteria (if any).

    Requirements:

    - no current Fellowship exists
    - no current FellowshipNomination exists
    - no 'not elected' decision in last 2 years
    - no invitation was turned down in the last 2 years
    """
    blocks = []
    if Fellowship.objects.active().regular_or_senior().filter(
            contributor__profile=profile).exists():
        blocks.append('This Profile is associated to an active Fellowship.')
    latest_nomination = FellowshipNomination.objects.filter(
        profile=profile).first()
    if latest_nomination:
        try:
            if (latest_nomination.decision.fixed_on +
                datetime.timedelta(days=730)) > timezone.now():
                if latest_nomination.decision.elected:
                    try:
                        if latest_nomination.invitation.declined:
                            blocks.append('Invitation declined less that 2 years ago. '
                                          'Wait to try again.')
                        else:
                             blocks.append('Already elected, invitation in process.')
                    except AttributeError:
                        blocks.append('Already elected, invitation pending.')
                blocks.append('Election failed less that 2 years ago. Must wait.')
        except AttributeError: # no decision yet
            blocks.append('This Profile is associated to an ongoing Nomination process.')
    return blocks if len(blocks) > 0 else None
