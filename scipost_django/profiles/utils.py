__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from submissions.models.referee_invitation import RefereeInvitation


def resolve_profile(view):
    """
    Decorator to resolve the profile of a user based on the request and pass in the `profile` kwarg to the view.
    """

    def wrapper(request, *args, **kwargs):
        if contributor := getattr(request.user, "contributor", None):
            profile = contributor.profile
        elif invitation_key := request.session.get("invitation_key", None):
            referee_invitation = RefereeInvitation.objects.filter(
                invitation_key=invitation_key
            ).first()
            profile = referee_invitation.profile if referee_invitation else None
        else:
            profile = None

        return view(request, profile=profile, *args, **kwargs)

    return wrapper
