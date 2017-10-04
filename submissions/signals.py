from django.contrib.auth.models import User, Group

from notifications.signals import notify


def notify_new_manuscript_submitted(sender, instance, created, **kwargs):
    """
    Notify the Editorial Administration about a new Submission submitted.
    """
    if created:
        administrators = User.objects.filter(groups__name='Editorial Administrators')
        for user in administrators:
            notify.send(sender=sender, recipient=user, actor=instance.submitted_by,
                        verb=' submitted a new manuscript.', target=instance)


def notify_new_editorial_recommendation(sender, instance, created, **kwargs):
    """
    Notify the Editorial Recommendation about a new Submission submitted.
    """
    if created:
        administrators = User.objects.filter(groups__name='Editorial Administrators')
        editor_in_charge = instance.submission.editor_in_charge
        for user in administrators:
            notify.send(sender=sender, recipient=user, actor=editor_in_charge,
                        verb=' formulated a new Editorial Recommendation.', target=instance)


def notify_new_editorial_assignment(sender, instance, created, **kwargs):
    """
    Notify a College Fellow about a new EIC invitation.
    """
    if created:
        administration = Group.objects.get(name='Editorial Administrators')
        if instance.accepted:
            # A new assignment is auto-accepted if user assigned himself or on resubmission.
            text = ' assigned you Editor-in-charge.'
        else:
            text = ' invited you to become Editor-in-charge.'
        notify.send(sender=sender, recipient=instance.to.user, actor=administration,
                    verb=text, target=instance)


def notify_new_referee_invitation(sender, instance, created, **kwargs):
    """
    Notify a Referee about a new refereeing invitation.
    """
    if created and instance.referee:
        notify.send(sender=sender, recipient=instance.referee.user,
                    actor=instance.submission.editor_in_charge,
                    verb=' would like to invite you to referee a Submission.', target=instance)
