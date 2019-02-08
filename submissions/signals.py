__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.models import User, Group

from notifications.constants import (
    NOTIFICATION_REFEREE_DEADLINE, NOTIFICATION_REFEREE_OVERDUE, NOTIFICATION_REPORT_UNFINISHED)
from notifications.models import Notification, FakeActors
from notifications.signals import notify


def notify_new_manuscript_submitted(sender, instance, created, **kwargs):
    """Notify the Editorial Administration about a new Submission submitted."""
    if created:
        administrators = User.objects.filter(groups__name='Editorial Administrators')
        for user in administrators:
            notify.send(
                sender=sender, recipient=user, actor=instance.submitted_by,
                verb=' submitted a new manuscript.', target=instance,
                url_code='editorial_page')


def notify_new_editorial_recommendation(sender, instance, created, **kwargs):
    """Notify the Editorial Recommendation about a new Submission submitted."""
    if created:
        administrators = User.objects.filter(groups__name='Editorial Administrators')
        editor_in_charge = instance.submission.editor_in_charge
        for user in administrators:
            notify.send(
                sender=sender, recipient=user, actor=editor_in_charge,
                verb=' formulated a new Editorial Recommendation.', target=instance,
                url_code='editorial_page')


def notify_eic_new_report(sender, instance, created, **kwargs):
    """Notify the Editor-in-charge about a new submitted Report."""
    editor_in_charge = instance.submission.editor_in_charge
    if editor_in_charge:
        notify.send(
            sender=sender, actor=instance.author, recipient=editor_in_charge.user,
            verb=' delivered a Report. Please vet it.', target=instance,
            url_code='editorial_page')


def notify_report_vetted(sender, instance, created, **kwargs):
    """Notify author that its Report has been vetted."""
    if instance.vetted_by == instance.submission.editor_in_charge:
        actor, __ = FakeActors.objects.get_or_create(name='Editor-in-charge')
    else:
        actor, __ = FakeActors.objects.get_or_create(name='Editorial Administration')

    txt = ' vetted your Report: %s.' % instance.get_status_display()
    notify.send(
        sender=sender, actor=actor, recipient=instance.author.user,
        verb=txt, target=instance)


def notify_submission_author_new_report(sender, instance, created, **kwargs):
    """Notify the Editor-in-charge about a new submitted Report."""
    actor, __ = FakeActors.objects.get_or_create(name='')  # Silence.
    notify.send(
        sender=sender, actor=instance.author, recipient=instance.submission.submitted_by.user,
        verb='A new Report has been delivered to your Submission.', target=instance)


def notify_new_editorial_assignment(sender, instance, created, **kwargs):
    """Notify a College Fellow about a new EIC invitation."""
    if created:
        administration = Group.objects.get(name='Editorial Administrators')
        if instance.accepted:
            # A new assignment is auto-accepted if user assigned himself or on resubmission.
            text = ' assigned you Editor-in-charge.'
        else:
            text = ' invited you to become Editor-in-charge.'
        notify.send(
            sender=sender, recipient=instance.to.user,
            actor=administration, verb=text, target=instance)


def notify_editor_assigned(sender, instance, created, **kwargs):
    """Notify Editorial Administration about a new assignment."""
    if instance.to:
        recipients = User.objects.filter(groups__name='Editorial Administrators')
        for recipient in recipients:
            # TO DO: Not filtered for possible admin-author conflict.
            notify.send(
                sender=sender, recipient=recipient, actor=instance.to, url_code='editorial_page',
                verb=' has accepted to act as Editor-in-charge.', target=instance.submission)


def notify_new_referee_invitation(sender, instance, created, **kwargs):
    """Notify a Referee about a new refereeing invitation."""
    if created and instance.referee:
        notify.send(sender=sender, recipient=instance.referee.user,
                    actor=instance.submission.editor_in_charge,
                    verb=' would like to invite you to referee a Submission.', target=instance)


def notify_invitation_cancelled(sender, instance, created, **kwargs):
    """Notify a Referee its invitation got cancelled."""
    if instance.referee:
        eic = instance.submission.editor_in_charge
        if eic and sender == eic.user:
            actor, __ = FakeActors.objects.get_or_create(name='Editor-in-charge')
        else:
            actor, __ = FakeActors.objects.get_or_create(name='Editorial Administration')
        notify.send(
            sender=sender, recipient=instance.referee.user, actor=actor,
            verb=' cancelled your referee invitation.', target=instance.submission)


def notify_eic_invitation_reponse(sender, instance, created, **kwargs):
    """Notify the EIC that a referee has responded to a RefInv."""
    eic = instance.submission.editor_in_charge
    if eic:
        txt = ' %s the refereeing invitation.' % ('accepted' if instance.accepted else 'declined')
        notify.send(
            sender=sender, recipient=eic.user, actor=eic.user, verb=txt,
            target=instance.submission, url_code='editorial_page')


def notify_new_communication(sender, instance, created, **kwargs):
    """Notify the receiver of the new Communication."""
    if not created:
        return

    if instance.comtype in ['AtoE', 'RtoE', 'StoE']:
        if instance.submission.editor_in_charge:
            recipients = [instance.submission.editor_in_charge.user]
        else:
            # No editor assigned yet.
            return
        if instance.comtype == 'StoE':
            actor, __ = FakeActors.objects.get_or_create(name='Editorial Administration')
        elif instance.comtype == 'AtoE':
            actor = instance.submission.submitted_by
        elif instance.comtype == 'RtoE':
            actor = instance.referee
        text = ' has sent a communication regarding a Submission you are Editor-in-charge for.'
        url_code = 'editorial_page'
    elif instance.comtype == 'EtoS':
        # To Editorial Administration
        recipients = User.objects.filter(groups__name='Editorial Administrators')
        actor, __ = FakeActors.objects.get_or_create(name='Editor-in-charge')
        text = ' has sent a communication to the Editorial Administration.'
        url_code = 'editorial_page'
    elif instance.comtype == 'EtoA':
        # Submitting author
        recipients = [instance.submission.submitted_by.user]
        actor, __ = FakeActors.objects.get_or_create(name='Editor-in-charge')
        text = ' has sent a communication regarding your Submission.'
        url_code = ''
    elif instance.comtype == 'EtoR':
        # To referee
        recipients = [instance.referee.user]
        actor, __ = FakeActors.objects.get_or_create(name='Editor-in-charge')
        text = ' has sent a communication regarding a Submission you have been invited to referee.'
        url_code = ''
    else:
        # Weird.
        return

    for recipient in recipients:
        notify.send(
            sender=sender, recipient=recipient, actor=actor, verb=text,
            target=instance, url_code=url_code)


def notify_unfinished_report(sender, instance, created, **kwargs):
    """Notify Referee he has an unfinished Report."""
    if not instance.author:
        return

    send_new = not Notification.objects.filter(
        recipient=instance.author.user, internal_type=NOTIFICATION_REPORT_UNFINISHED).unread_or_today().exists()
    if send_new:
        # User doesn't already have a notification to remind him.
        administration = Group.objects.get(name='Editorial Administrators')
        notify.send(
            sender=sender, recipient=instance.author.user, actor=administration,
            verb=' would like to remind you that you have an unfinished Report.',
            target=instance.submission, type=NOTIFICATION_REPORT_UNFINISHED,
            url_code='report_form')


def notify_invitation_approaching_deadline(sender, instance, created, **kwargs):
    """Notify Referee its unfinished duty is approaching the deadline."""
    if instance.referee:
        notifications = Notification.objects.filter(
            recipient=instance.referee.user, internal_type=NOTIFICATION_REFEREE_DEADLINE).unread_or_today()
        if not notifications.exists():
            # User doesn't already have a notification to remind him.
            administration = Group.objects.get(name='Editorial Administrators')
            notify.send(
                sender=sender, recipient=instance.referee.user, actor=administration,
                verb=(
                    ' would like to remind you that your Refereeing Task is approaching'
                    ' its deadline, please submit your Report'),
                target=instance.submission, type=NOTIFICATION_REFEREE_DEADLINE)


def notify_invitation_overdue(sender, instance, created, **kwargs):
    """Notify Referee its unfinished duty is overdue."""
    if instance.referee:
        notifications = Notification.objects.filter(
            recipient=instance.referee.user, internal_type=NOTIFICATION_REFEREE_OVERDUE).unread_or_today()
        if not notifications.exists():
            # User doesn't already have a notification to remind him.
            administration = Group.objects.get(name='Editorial Administrators')
            notify.send(
                sender=sender, recipient=instance.referee.user, actor=administration,
                verb=(
                    ' would like to remind you that your Refereeing Task is overdue, '
                    'please submit your Report'),
                target=instance.submission, type=NOTIFICATION_REFEREE_OVERDUE)


def notify_manuscript_accepted(sender, instance, created, **kwargs):
    """Notify authors about their manuscript decision.

    instance --- Submission
    """
    college = Group.objects.get(name='Editorial College')
    authors = User.objects.filter(contributor__submissions=instance)
    for user in authors:
        notify.send(
            sender=sender, recipient=user, actor=college,
            verb=' has accepted your manuscript for publication.', target=instance)
