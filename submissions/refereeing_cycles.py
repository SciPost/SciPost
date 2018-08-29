__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import datetime

from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.html import format_html

from . import constants
from .utils import RequiredActionsDict


class BaseAction:
    """An item in the RequiredActionsDict dictionary for the Submission refereeing cycle."""
    txt = ''
    url = '#'
    submission = None

    def __init__(self, object=None, **kwargs):
        self._objects = []
        self.add(object)

        self.id = object.__class__.__name__ if object else self.__class__.__name__

    def add(self, object=None):
        if object:
            self._objects.append(object)

    def _format_text(self, text, obj=None):
        if obj is None and self._objects:
            obj = self._objects[0]

        timedelta = datetime.timedelta()
        deadline = datetime.timedelta()

        if hasattr(obj, 'date_invited'):
            timedelta = timezone.now() - obj.date_invited
        if hasattr(obj, 'submission'):
            deadline = obj.submission.reporting_deadline - timezone.now()

        return text.format(
            count=len(self._objects),
            object=obj.__class__.__name__,
            author=obj.author.formal_str if hasattr(obj, 'author') and obj.author else '',
            referee=obj.referee_str if hasattr(obj, 'referee_str') else '',
            days=timedelta.days,
            deadline=deadline.days,
            deadline_min=-deadline.days,
            url=self.url)

    def as_text(self):
        return ' '.join([e for e in self])

    def __iter__(self):
        if self._objects:
            for obj in self._objects:
                yield format_html(self._format_text(self.txt))
        else:
            yield format_html(self._format_text(self.txt))

    def __str__(self):
        return self.as_text()


class VettingAction(BaseAction):
    txt = '{author} has delivered a {object}. <a href="{url}">Please vet it</a>.'

    @property
    def url(self):
        return '{}#current-contributions'.format(reverse(
            'submissions:editorial_page', args=(self.submission.preprint.identifier_w_vn_nr,)))


class NoRefereeResponseAction(BaseAction):
    txt = (
        'Referee {referee} has not responded for {days} days.'
        ' Consider sending a reminder or cancelling the invitation.')


class DeadlineAction(BaseAction):
    txt = (
        'Referee {referee} has accepted to send a Report '
        '(with {deadline} days left), but not yet delivered it. Consider sending a reminder.')


class OverdueAction(BaseAction):
    txt = (
        'Referee {referee} has accepted to send a Report '
        '({deadline_min} days overdue), but not yet delivered it. Consider sending a reminder.')


class ChoiceCycleAction(BaseAction):
    txt = 'Choose the submission cycle to proceed with.'


class NoEICRecommendationAction(BaseAction):
    @property
    def txt(self):
        if not self.submission.reports.non_draft().exists():
            txt = (
                'The refereeing deadline has passed and you have received no Reports yet.'
                ' Please <a href="{url}">extend the reporting deadline</a> '
                'and consider sending a reminder to your referees.')
        else:
            txt = (
                'The refereeing deadline has passed. Please either '
                '<a href="{url}">extend it</a>, '
                'or formulate your Editorial Recommendation.')
        return txt

    @property
    def url(self):
        return '{}#reporting-deadline'.format(reverse(
            'submissions:editorial_page', args=(self.submission.preprint.identifier_w_vn_nr,)))


class NeedRefereesAction(BaseAction):
    def __init__(self, object=None, **kwargs):
        self.minimum_number_of_referees = kwargs.pop('minimum_number_of_referees')
        self.current_number_of_referees = kwargs.pop('current_number_of_referees')
        super().__init__(object, **kwargs)

    @property
    def txt(self):
        if self.current_number_of_referees == 0:
            text = 'No Referees have yet been invited.'
        elif self.current_number_of_referees == 1:
            text = 'Only 1 Referee has yet been invited.'
        else:
            text = 'Only %i Referees have yet been invited.' % self.current_number_of_referees
        text += ' At least {minimum} should be. <a href="{url}">Invite a referee here</a>.'.format(
            minimum=self.minimum_number_of_referees,
            url=reverse(
                'submissions:select_referee', args=(self.submission.preprint.identifier_w_vn_nr,)))
        return text


class BaseCycle:
    """A base blueprint for the Submission refereeing cycle.

    The refereeing process may be defined differently for every cycle class by its own
    specific properties. The cycle class will then take care of the required actions,
    permissions and the overall refereeing process.
    """

    days_for_refereeing = 28
    minimum_number_of_referees = 3
    can_invite_referees = True

    def __init__(self, submission, current_user=None):
        self._submission = submission
        self._required_actions = None
        self._current_user = current_user

    @property
    def required_actions(self):
        if self._required_actions is None:
            self.update_required_actions()
        return self._required_actions

    def has_required_actions(self):
        return bool(self.required_actions)

    def add_action(self, action):
        if action not in self.required_actions:
            self._required_actions[action] = action
        else:
            self._required_actions[action].add(action)
        self._required_actions[action].submission = self._submission

    def update_required_actions(self):
        """Gather the required actions list and populate self._required_actions."""
        self._required_actions = RequiredActionsDict()

        if not self._submission.refereeing_cycle:
            # Submission is a resubmission: EIC has to determine which cycle to proceed with.
            self.add_action(ChoiceCycleAction())
            return  # If no cycle is chosen. Make this a first priority!

        # The EIC is late with formulating a Recommendation.
        if self._submission.eic_recommendation_required:
            if self._submission.reporting_deadline_has_passed:
                self.add_action(NoEICRecommendationAction())

        # Submission is a resubmission: EIC has to determine which cycle to proceed with.
        comments_to_vet = self._submission.comments.awaiting_vetting().values_list('id')
        for comment in comments_to_vet:
            self.add_action(VettingAction(comment))

        reports_to_vet = self._submission.reports.awaiting_vetting()
        for report in reports_to_vet:
            self.add_action(VettingAction(report))

        if self.can_invite_referees and self._submission.in_refereeing_phase:
            # Referees required in this cycle.
            referee_invitations_count = self._submission.referee_invitations.non_cancelled().count()

            # The current number of referees does not meet the minimum number of referees yet.
            if referee_invitations_count < self.minimum_number_of_referees:
                self.add_action(NeedRefereesAction(
                    current_number_of_referees=referee_invitations_count,
                    minimum_number_of_referees=self.minimum_number_of_referees))

        referee_invitations = self._submission.referee_invitations.needs_attention()
        for referee_invitation in referee_invitations:
            if referee_invitation.needs_response:
                # Invited, but no response
                self.add_action(NoRefereeResponseAction(referee_invitation))
            elif referee_invitation.is_overdue:
                self.add_action(OverdueAction(referee_invitation))
            elif referee_invitation.needs_fulfillment_reminder:
                self.add_action(DeadlineAction(referee_invitation))

    def as_text(self):
        """Return a *short* description of the current status of the submission cycle."""
        texts = []

        recommendation = self._submission.eicrecommendations.active().last()
        if recommendation:
            texts.append('Thank you for formulating your Editorial Recommendation.')
            if recommendation.status == constants.VOTING_IN_PREP:
                texts.append('The Editorial Administration is now preparing it for voting.')
            elif recommendation.status == constants.PUT_TO_VOTING:
                texts.append('It is now put to voting in the college.')

        if self._submission.status == constants.STATUS_RESUBMITTED:
            new_sub_id = self._submission.get_latest_version().preprint.identifier_w_vn_nr
            txt = (
                'The Submission has been resubmitted as {identifier},'
                ' <a href="{url}">go to its editorial page</a>.')
            texts.append(txt.format(
                url=reverse('submissions:editorial_page', args=(new_sub_id,)),
                identifier=new_sub_id))
        elif self._submission.status == constants.STATUS_ACCEPTED:
            texts.append('The SciPost production team is working on the proofs for publication.')
        elif self._submission.status == constants.STATUS_REJECTED:
            texts.append('The Submission is rejected for publication.')
        elif self._submission.status == constants.STATUS_WITHDRAWN:
            texts.append('The authors have withdrawn the Submission.')
        elif self._submission.status == constants.STATUS_PUBLISHED:
            texts.append('The Submission has been published as <a href="{url}">{doi}</a>.'.format(
                url=self._submission.publication.get_absolute_url(),
                doi=self._submission.publication.doi_label))
        elif self._submission.status == constants.STATUS_EIC_ASSIGNED:
            if not self._submission.in_refereeing_phase:
                if recommendation:
                    texts.append('The refereeing round is closed.')
                else:
                    texts.append((
                        'The refereeing round is closed '
                        'and you have not formulated an Editorial Recommendation.'))

        if not self.required_actions and not texts:
            texts.append('No action required.')
        elif self.required_actions:
            texts.append(
                '<strong>Please see your required actions below.</strong>')
        return format_html(' '.join(texts))

    def __str__(self):
        return self.as_text()

    def reset_refereeing_round(self):
        """Set the Submission status to EIC_ASSIGNED and reset the reporting deadline."""
        from .models import Submission  # Prevent circular import errors
        if self._submission.status in [constants.STATUS_INCOMING, constants.STATUS_UNASSIGNED]:
            Submission.objects.filter(id=self._submission.id).update(
                status=constants.STATUS_EIC_ASSIGNED)

        deadline = timezone.now() + datetime.timedelta(days=self.days_for_refereeing)
        Submission.objects.filter(id=self._submission.id).update(reporting_deadline=deadline)

    def reinvite_referees(self, referees, request):
        """Duplicate and reset RefereeInvitations and send `reinvite` mail.

        referees - (list of) RefereeInvitation instances
        """
        from mails.utils import DirectMailUtil
        SubmissionUtils.load({'submission': self._submission})
        for referee in referees:
            invitation = referee
            invitation.pk = None  # Duplicate, do not remove the old invitation
            invitation.submission = self._submission
            invitation.reset_content()
            invitation.date_invited = timezone.now()
            invitation.save()
            mail_sender = DirectMailUtil(
                mail_code='referees/reinvite_contributor_to_referee', instance=invitation)
            mail_sender.send()

            # SubmissionUtils.load({'invitation': invitation}, request)
            # SubmissionUtils.reinvite_referees_email()


class RegularCycle(BaseCycle):
    pass
