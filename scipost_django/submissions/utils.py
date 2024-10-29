__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
import itertools
import os
import re
import subprocess
from typing import TYPE_CHECKING

from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template import Context, Template

from common.utils.urls import absolute_reverse

from .constants import (
    ED_COMM_CHOICES,
    ED_COMM_PARTIES,
    STATUS_VETTED,
    STATUS_UNCLEAR,
    STATUS_INCORRECT,
    STATUS_NOT_USEFUL,
    STATUS_NOT_ACADEMIC,
)

from scipost.utils import EMAIL_FOOTER
from common.utils import get_current_domain, BaseMailUtil

domain = get_current_domain()


if TYPE_CHECKING:
    from submissions.models.communication import EditorialCommunication
    from scipost.models import Contributor
    from submissions.models import RefereeInvitation


class SubmissionUtils(BaseMailUtil):
    mail_sender = f"submissions@{domain}"
    mail_sender_title = "SciPost Editorial Admin"

    @classmethod
    def send_EIC_appointment_email(cls):
        """Requires loading 'assignment' attribute."""
        r = cls.assignment
        email_text = (
            "Dear "
            + cls.assignment.to.profile.get_title_display()
            + " "
            + cls.assignment.to.user.last_name
            + ", \n\nThank you for accepting to become Editor-in-charge "
            "of the SciPost Submission\n\n"
            + cls.assignment.submission.title
            + " by "
            + cls.assignment.submission.author_list
            + "."
            "\n\nYou can take your editorial actions from the editorial page "
            f"https://{domain}/submission/editorial_page/"
            + cls.assignment.submission.preprint.identifier_w_vn_nr
            + " (also accessible from your personal page "
            f"https://{domain}/personal_page under the Editorial Actions tab). "
            "In particular, unless you choose to directly formulate a Recommendation, "
            "you should now start a refereeing round and invite at least 3 referees; "
            "you might want to make sure you are aware of the "
            "detailed procedure described in the Editorial College by-laws at "
            f"https://{domain}/EdCol_by-laws."
            "\n\nMany thanks in advance for your collaboration,"
            "\n\nThe SciPost Team."
        )
        email_text_html = (
            "<p>Dear {{ title }} {{ last_name }},</p>"
            "<p>Thank you for accepting to become Editor-in-charge "
            "of the SciPost Submission</p>"
            "<p>{{ sub_title }}</p>"
            "\n<p>by {{ author_list }}.</p>"
            "\n<p>You can take your editorial actions from the "
            f'<a href="https://{domain}/submission/editorial_page/'
            '{{ identifier_w_vn_nr }}">editorial page</a> '
            "(also accessible from your "
            f'<a href="https://{domain}/personal_page">personal page</a> '
            "under the Editorial Actions tab).</p>"
            "\n<p>In particular, unless you choose to directly formulate a Recommendation, "
            "you should now start a refereeing round and invite at least 3 referees; "
            "you might want to make sure you are aware of the "
            "detailed procedure described in the "
            f'<a href="https://{domain}/EdCol_by-laws">Editorial College by-laws</a>.</p>'
            "<p>Many thanks in advance for your collaboration,</p>"
            "<p>The SciPost Team.</p>"
        )
        email_context = {
            "title": cls.assignment.to.profile.get_title_display(),
            "last_name": cls.assignment.to.user.last_name,
            "sub_title": cls.assignment.submission.title,
            "author_list": cls.assignment.submission.author_list,
            "identifier_w_vn_nr": cls.assignment.submission.preprint.identifier_w_vn_nr,
        }
        email_text_html += "<br/>" + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(Context(email_context))
        emailmessage = EmailMultiAlternatives(
            "SciPost: assignment as EIC",
            email_text,
            f"SciPost Editorial Admin <submissions@{domain}>",
            [cls.assignment.to.user.email],
            bcc=[f"submissions@{domain}"],
            reply_to=[f"submissions@{domain}"],
        )
        emailmessage.attach_alternative(html_version, "text/html")
        emailmessage.send(fail_silently=False)

    @classmethod
    def send_author_assignment_passed_email(cls):
        """Requires loading 'assignment' attribute."""
        email_text = (
            "Dear "
            + cls.assignment.submission.submitted_by.profile.get_title_display()
            + " "
            + cls.assignment.submission.submitted_by.user.last_name
            + ", \n\nWe are pleased to inform you that your recent Submission to SciPost,\n\n"
            + cls.assignment.submission.title
            + " by "
            + cls.assignment.submission.author_list
            + "\n\nhas successfully passed the assignment stage. "
            "\n\nA Submission Page has been activated at "
            f"https://{domain}/submission/"
            + cls.assignment.submission.preprint.identifier_w_vn_nr
            + (
                " and a refereeing round has been started, with deadline "
                "currently set at "
                + datetime.datetime.strftime(
                    cls.assignment.submission.reporting_deadline, "%Y-%m-%d"
                )
                if cls.assignment.submission.reporting_deadline
                else ""
            )
            + ".\n\n"
            "During the refereeing round, you are welcome to provide replies to any "
            "Report or Comment posted on your Submission (you can do so from the "
            "Submission Page; you will be informed by email of any such Report or "
            "Comment being delivered). In order to facilitate the work of the "
            "Editorial College, we recommend limiting these replies to short "
            "to-the-point clarifications of any issue raised on your manuscript.\n\n"
            "Please wait for the Editor-in-charge's Editorial Recommendation "
            "before any resubmission of your manuscript."
            "\n\nTo facilitate metadata handling, we recommend that all authors "
            "have an ORCID id (easily obtained from https://orcid.org), "
            "and be registered as SciPost Contributors. Could we please ask you "
            "(and your coathors, if any) to ensure that this is the case?"
            "\n\nWe thank you very much for your contribution."
            "\n\nSincerely," + "\n\nThe SciPost Team."
        )
        email_text_html = (
            "<p>Dear {{ title }} {{ last_name }},</p>"
            "<p>We are pleased to inform you that your recent Submission to SciPost,</p>"
            "<p>{{ sub_title }}</p>"
            "\n<p>by {{ author_list }}</p>"
            "\n<p>has successfully passed the assignment stage.</p>"
            f'\n<p>A <a href="https://{domain}/submission/'
            + '{{ identifier_w_vn_nr }}">'
            "Submission Page</a> has been activated"
            + (
                " and a refereeing round has been started, with deadline "
                "currently set at {{ deadline }}.</p>"
                if cls.assignment.submission.reporting_deadline
                else ""
            )
            + "<h3>Further procedure</h3>"
            "<p>During the refereeing round, you are welcome to provide replies to any "
            "Report or Comment posted on your Submission (you can do so from the "
            "Submission Page; you will be informed by email of any such Report or "
            "Comment being delivered). In order to facilitate the work of the "
            "Editorial College, we recommend limiting these replies to short "
            "to-the-point clarifications of any issue raised on your manuscript.</p>"
            "<p>Please wait for the Editor-in-charge's Editorial Recommendation "
            "before any resubmission of your manuscript.</p>"
            "<h4>Author information</h4>"
            "<p>To facilitate metadata handling, we recommend that all authors "
            'have an ORCID id (easily obtained from <a href="https://orcid.org">orcid.org</a>), '
            "and be registered as SciPost Contributors. Could we please ask you "
            "(and your coathors, if any) to ensure that this is the case?</p>"
            "<p>We thank you very much for your contribution.</p>"
            "<p>Sincerely,</p>"
            "<p>The SciPost Team.</p>"
        )
        email_context = {
            "title": cls.assignment.submission.submitted_by.profile.get_title_display(),
            "last_name": cls.assignment.submission.submitted_by.user.last_name,
            "sub_title": cls.assignment.submission.title,
            "author_list": cls.assignment.submission.author_list,
            "identifier_w_vn_nr": cls.assignment.submission.preprint.identifier_w_vn_nr,
            "deadline": (
                datetime.datetime.strftime(
                    cls.assignment.submission.reporting_deadline, "%Y-%m-%d"
                )
                if cls.assignment.submission.reporting_deadline
                else ""
            ),
        }
        email_text_html += "<br/>" + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(Context(email_context))
        emailmessage = EmailMultiAlternatives(
            "SciPost: assignment passed",
            email_text,
            f"SciPost Editorial Admin <submissions@{domain}>",
            [cls.assignment.submission.submitted_by.user.email],
            bcc=[f"submissions@{domain}"],
            reply_to=[f"submissions@{domain}"],
        )
        emailmessage.attach_alternative(html_version, "text/html")
        emailmessage.send(fail_silently=False)

    @classmethod
    def send_unreg_ref_reminder_email(cls):
        """
        This method is used to remind a referee who has not yet responded.
        It is used for unregistered referees only.
        It is called from the ref_invitation_reminder method in submissions/views.py.
        """
        email_text = (
            "Dear " + cls.invitation.referee.formal_name + ",\n\n"
            "On behalf of the Editor-in-charge "
            + cls.invitation.submission.editor_in_charge.profile.formal_name
            + ", we would like to cordially remind you of our recent request to referee\n\n"
            + cls.invitation.submission.title
            + " by "
            + cls.invitation.submission.author_list
            + "."
        )
        email_text_html = (
            "<p>Dear {{ referee_formal_name }},</p>"
            "<p>On behalf of the Editor-in-charge {{ EIC_formal_name }}, "
            "we would like to cordially remind you of our recent request to referee</p>"
            "<p>{{ sub_title }}</p>"
            "\n<p>by {{ author_list }}.</p>"
        )
        email_text += (
            "\n\nWe would also like to renew "
            "our invitation to become a Contributor on SciPost "
            "(our records show that you are not yet registered); "
            "your partially pre-filled registration form is still available at\n\n"
            f"https://{domain}/invitation/" + cls.invitation.invitation_key + "\n\n"
            "after which your registration will be activated, giving you full access to "
            "the portal's facilities (in particular allowing you to "
            "provide referee reports).\n\n"
            "To ensure timely processing of the submission (out of respect for the authors), "
            "we would appreciate a quick accept/decline response from you, "
            "ideally within the next 2 days.\n\n"
            "If you are not able to provide a Report, you can quickly let us know by simply "
            f"navigating to \n\nhttps://{domain}/submissions/decline_ref_invitation/"
            + cls.invitation.invitation_key
            + "\n\n"
            "If you are able to provide a Report, you can confirm this after registering "
            "and logging in (you will automatically be prompted for a confirmation). "
            "Your report can thereafter be submitted by simply clicking on "
            'the "Contribute a Report" link at '
            f"https://{domain}/submission/"
            + cls.invitation.submission.preprint.identifier_w_vn_nr
            + (
                " before the reporting deadline (currently set at "
                + datetime.datetime.strftime(
                    cls.invitation.submission.reporting_deadline, "%Y-%m-%d"
                )
                if cls.invitation.submission.reporting_deadline
                else ""
            )
            + "; your report will be automatically recognized as an invited report). "
            "You might want to make sure you are familiar with our refereeing code of conduct "
            f"https://{domain}/journals/journals_terms_and_conditions and with the "
            f"editorial procedure https://{domain}/submissions/editorial_procedure."
            "\n\nWe very much hope we can count on your expertise,"
            "\n\nMany thanks in advance,\n\nThe SciPost Team"
        )
        email_text_html += (
            "\n<p>We would also like to renew "
            "our invitation to become a Contributor on SciPost "
            "(our records show that you are not yet registered); "
            "your partially pre-filled "
            f'<a href="https://{domain}' + '/invitation/{{ invitation_key }}">'
            "registration form</a> is still available, "
            "after which your registration will be activated, giving you full access to "
            "the portal's facilities (in particular allowing you to provide referee reports).</p>"
            "<p>To ensure timely processing of the submission (out of respect for the authors), "
            "we would appreciate a quick accept/decline response from you, "
            "ideally within the next 2 days.</p>"
            "<p>If you are <strong>not</strong> able to provide a Report, "
            "you can quickly let us know by simply "
            f'<a href="https://{domain}'
            + '/submissions/decline_ref_invitation/{{ invitation_key }}">'
            "clicking here</a>.</p>"
            "<p>If you are able to provide a Report, you can confirm this after registering "
            "and logging in (you will automatically be prompted for a confirmation). "
            "Your report can thereafter be submitted by simply clicking on "
            'the "Contribute a Report" link at '
            f'the <a href="https://{domain}' + '/submission/{{ identifier_w_vn_nr }}">'
            "Submission's page</a>"
            + (
                " before the reporting deadline (currently set at " "{{ deadline }}"
                if cls.invitation.submission.reporting_deadline
                else ""
            )
            + "; your report will be automatically recognized as an invited report).</p>"
            "\n<p>You might want to make sure you are familiar with our "
            f'<a href="https://{domain}/journals/journals_terms_and_conditions">'
            "refereeing code of conduct</a> and with the "
            f'<a href="https://{domain}/submissions/editorial_procedure">'
            "editorial procedure</a>.</p>"
            "<p>We very much hope we can count on your expertise,</p>"
            "<p>Many thanks in advance,</p>"
            "<p>The SciPost Team</p>"
        )
        email_context = {
            "referee_formal_name": cls.invitation.referee.formal_name,
            "EIC_formal_name": cls.invitation.submission.editor_in_charge.profile.formal_name,
            "sub_title": cls.invitation.submission.title,
            "author_list": cls.invitation.submission.author_list,
            "identifier_w_vn_nr": cls.invitation.submission.preprint.identifier_w_vn_nr,
            "deadline": (
                datetime.datetime.strftime(
                    cls.invitation.submission.reporting_deadline, "%Y-%m-%d"
                )
                if cls.invitation.submission.reporting_deadline
                else ""
            ),
            "invitation_key": cls.invitation.invitation_key,
        }
        email_text_html += "<br/>" + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(Context(email_context))
        emailmessage = EmailMultiAlternatives(
            "SciPost: reminder (refereeing request and registration invitation)",
            email_text,
            f"SciPost Refereeing <refereeing@{domain}>",
            [cls.invitation.email_address],
            bcc=[
                cls.invitation.submission.editor_in_charge.user.email,
                f"refereeing@{domain}",
            ],
            reply_to=[f"refereeing@{domain}"],
        )
        emailmessage.attach_alternative(html_version, "text/html")
        emailmessage.send(fail_silently=False)

    @classmethod
    def send_ref_reminder_email(cls):
        """
        This method is used to remind a referee who has not yet responded.
        It is used for registered Contributors only.
        It is called from the ref_invitation_reminder method in submissions/views.py.
        """
        email_text = (
            "Dear " + cls.invitation.referee.formal_name + ",\n\n"
            "On behalf of the Editor-in-charge "
            + cls.invitation.submission.editor_in_charge.profile.formal_name
            + ", we would like to cordially remind you of our recent request to referee\n\n"
            + cls.invitation.submission.title
            + " by "
            + cls.invitation.submission.author_list
            + "."
        )
        email_text_html = (
            "<p>Dear {{ referee_formal_name }},</p>"
            "<p>On behalf of the Editor-in-charge {{ EIC_formal_name }}, "
            "we would like to cordially remind you of our recent request to referee</p>"
            "<p>{{ sub_title }}</p>"
            "\n<p>by {{ author_list }}.</p>"
        )
        if cls.invitation.accepted is None:
            email_text += (
                "\n\nPlease visit "
                f"https://{domain}/submissions/accept_or_decline_ref_invitations "
                "(login required) as soon as possible (ideally within the next 2 days) "
                "in order to accept or decline this invitation."
            )
            email_text_html += (
                "\n<p>Please "
                f'<a href="https://{domain}/submissions/accept_or_decline_ref_invitations">'
                "accept or decline the invitation</a> "
                "(login required) as soon as possible (ideally within the next 2 days) "
                "in order to ensure rapid processing of the submission."
            )
        email_text += (
            "\n\nYour report can be submitted by simply clicking on "
            'the "Contribute a Report" link at '
            f"https://{domain}/submission/"
            + cls.invitation.submission.preprint.identifier_w_vn_nr
            + (
                " before the reporting deadline (currently set at "
                + datetime.datetime.strftime(
                    cls.invitation.submission.reporting_deadline, "%Y-%m-%d"
                )
                if cls.invitation.submission.reporting_deadline
                else ""
            )
            + "; your report will be automatically recognized as an invited report). "
            "You might want to make sure you are familiar with our refereeing code of conduct "
            f"https://{domain}/journals/journals_terms_and_conditions and with the "
            f"editorial procedure https://{domain}/submissions/editorial_procedure."
            "\n\nWe very much hope we can count on your expertise,"
            "\n\nMany thanks in advance,\n\nThe SciPost Team"
        )
        email_text_html += (
            "\n<p>Your report can be submitted by simply clicking on "
            'the "Contribute a Report" link at '
            f'the <a href="https://{domain}' + '/submission/{{ identifier_w_vn_nr }}">'
            "Submission's page</a>"
            + (
                " before the reporting deadline (currently set at {{ deadline }})"
                if cls.invitation.submission.reporting_deadline
                else ""
            )
            + "; your report will be automatically recognized as an invited report).</p>"
            "\n<p>You might want to make sure you are familiar with our "
            f'<a href="https://{domain}/journals/journals_terms_and_conditions">'
            "refereeing code of conduct</a> and with the "
            f'<a href="https://{domain}/submissions/editorial_procedure">'
            "editorial procedure</a>.</p>"
            "<p>We very much hope we can count on your expertise,</p>"
            "<p>Many thanks in advance,</p>"
            "<p>The SciPost Team</p>"
        )
        email_context = {
            "referee_formal_name": cls.invitation.referee.formal_name,
            "EIC_formal_name": cls.invitation.submission.editor_in_charge.profile.formal_name,
            "sub_title": cls.invitation.submission.title,
            "author_list": cls.invitation.submission.author_list,
            "identifier_w_vn_nr": cls.invitation.submission.preprint.identifier_w_vn_nr,
            "deadline": (
                datetime.datetime.strftime(
                    cls.invitation.submission.reporting_deadline,
                    "%Y-%m-%d",
                )
                if cls.invitation.submission.reporting_deadline
                else ""
            ),
        }
        email_text_html += "<br/>" + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(Context(email_context))
        emailmessage = EmailMultiAlternatives(
            "SciPost: reminder (refereeing request)",
            email_text,
            f"SciPost Refereeing <refereeing@{domain}>",
            [cls.invitation.email_address],
            bcc=[
                cls.invitation.submission.editor_in_charge.user.email,
                f"refereeing@{domain}",
            ],
            reply_to=[f"refereeing@{domain}"],
        )
        emailmessage.attach_alternative(html_version, "text/html")
        emailmessage.send(fail_silently=False)

    @classmethod
    def send_ref_cancellation_email(cls):
        """
        This method is used to inform a referee that his/her services are no longer required.
        It is called from the _hx_cancel_ref_invitation method in submissions/views.py.
        """
        if getattr(cls, "invitation", None) is None:
            raise ValueError(
                "The RefereeInvitation is missing. Please `load()` it first."
            )

        cls.invitation: "RefereeInvitation"
        email_text = (
            "Dear " + cls.invitation.referee.formal_name + ",\n\n"
            "On behalf of the Editor-in-charge "
            + cls.invitation.submission.editor_in_charge.profile.formal_name
            + ", we would like to inform you that your report on\n\n"
            + cls.invitation.submission.title
            + " by "
            + cls.invitation.submission.author_list
            + "\n\nis no longer required."
            "\n\nWe very much hope we can count on your expertise "
            "at some other point in the future,"
            "\n\nMany thanks for your time,\n\nThe SciPost Team"
        )
        email_text_html = (
            "<p>Dear {{ referee_formal_name }},</p>"
            "<p>On behalf of the Editor-in-charge {{ EIC_formal_name }}, "
            "we would like to inform you that your report on</p>"
            "<p>{{ sub_title }}</p>"
            "\n<p>by {{ author_list }}</p>"
            "\n<p>is no longer required.</p>"
            "<p>We very much hope we can count on your expertise "
            "at some other point in the future,</p>"
            "<p>Many thanks for your time,</p>"
            "<p>The SciPost Team</p>"
        )
        if not cls.invitation.to_registered_referee:
            email_text += (
                "\n\nP.S.: We would also like to renew "
                "our invitation to become a Contributor on SciPost "
                "(our records show that you are not yet registered); "
                "your partially pre-filled registration form is still available at\n\n"
                f"https://{domain}/invitation/" + cls.invitation.invitation_key + "\n\n"
                "after which your registration will be activated, giving you full access to "
                "the portal's facilities (in particular allowing you to provide referee reports)."
            )
            email_text_html += (
                "\n<br/><p>P.S.: We would also like to renew "
                "our invitation to become a Contributor on SciPost "
                "(our records show that you are not yet registered); "
                "your partially pre-filled "
                f'<a href="https://{domain}' + '/invitation/{{ invitation_key }}">'
                "registration form</a> is still available "
                "after which your registration will be activated, giving you full access to "
                "the portal's facilities (in particular allowing you to provide referee reports).</p>"
            )
        email_context = {
            "referee_formal_name": cls.invitation.referee.formal_name,
            "EIC_formal_name": cls.invitation.submission.editor_in_charge.profile.formal_name,
            "sub_title": cls.invitation.submission.title,
            "author_list": cls.invitation.submission.author_list,
            "invitation_key": cls.invitation.invitation_key,
        }
        email_text_html += "<br/>" + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(Context(email_context))
        emailmessage = EmailMultiAlternatives(
            "SciPost: report no longer needed",
            email_text,
            f"SciPost Refereeing <refereeing@{domain}>",
            [cls.invitation.email_address],
            bcc=[
                cls.invitation.submission.editor_in_charge.user.email,
                f"refereeing@{domain}",
            ],
            reply_to=[f"refereeing@{domain}"],
        )
        emailmessage.attach_alternative(html_version, "text/html")
        emailmessage.send(fail_silently=False)

    @classmethod
    def acknowledge_report_email(cls):
        """Requires loading 'report' attribute."""
        email_text = (
            "Dear "
            + cls.report.author.profile.get_title_display()
            + " "
            + cls.report.author.user.last_name
            + ","
            "\n\nMany thanks for your Report on Submission\n\n"
            + cls.report.submission.title
            + " by "
            + cls.report.submission.author_list
            + "."
        )
        email_text_html = (
            "<p>Dear {{ ref_title }} {{ ref_last_name }},</p>"
            "<p>Many thanks for your Report on Submission</p>"
            "<p>{{ sub_title }}</p>\n<p>by {{ author_list }}.</p>"
        )
        if cls.report.status == STATUS_VETTED:
            email_text += (
                "\n\nYour Report has been vetted through and is viewable at "
                f"https://{domain}/submissions/"
                + cls.report.submission.preprint.identifier_w_vn_nr
                + "."
            )
            email_text_html += (
                "\n<p>Your Report has been vetted through and is viewable at "
                f'the <a href="https://{domain}/submissions/'
                "{{ identifier_w_vn_nr }}\">Submission's page</a>.</p>"
            )
            if not cls.report.anonymous:
                email_text += (
                    "\n\nPlease note that your Report is not anonymous and thus your identity will be publicly visible. "
                    "You may anonymize your Report within 24 hours at "
                    f"https://{domain}/submissions/"
                    + cls.report.submission.preprint.identifier_w_vn_nr
                    + f"#report_{cls.report.report_nr}."
                    "\n\nIf you choose to do so, your identity will be immediately hidden from the public. "
                    "However, kindly understand that SciPost cannot guarantee that this information "
                    "has not already been saved by unaffiliated third-parties during the time in which is was public."
                )
                email_text_html += (
                    "\n<p>Please note that your Report is not anonymous and thus your identity will be publicly visible. "
                    f'You may anonymize your Report within 24 hours at the <a href="https://{domain}/submissions/"'
                    f"{{ identifier_w_vn_nr }}//#report_{cls.report.report_nr}\">Submission's page</a>.</p>"
                    "<p>If you choose to do so, your identity will be immediately hidden from the public. "
                    "However, kindly understand that SciPost cannot guarantee that this information "
                    "has not already been saved by unaffiliated third-parties during the time in which is was public.</p>"
                )
        else:
            email_text += (
                "\n\nYour Report has been reviewed by the Editor-in-charge of the Submission, "
                "who decided not to admit it for online posting, citing the reason: "
                + cls.report.get_status_display()
                + "."
                " We copy the text entries of your report below for your convenience, "
                "if ever you wish to reformulate it and resubmit it."
            )
            email_text_html += (
                "\n<p>Your Report has been reviewed by the Editor-in-charge of the Submission, "
                "who decided not to admit it for online posting, citing the reason: "
                "{{ refusal_reason }}.</p>"
                "\n<p>We copy the text entries of your report below for your convenience, "
                "if ever you wish to reformulate it and resubmit it.</p>"
            )
        email_text += "\n\nMany thanks for your collaboration," "\n\nThe SciPost Team."
        email_text_html += (
            "<p>Many thanks for your collaboration,</p>" "<p>The SciPost Team.</p>"
        )
        if cls.report.status != STATUS_VETTED:
            if cls.email_response is not None:
                email_text += "\n\nAdditional info from the Editor-in-charge: \n"
                email_text += cls.email_response
                email_text_html += (
                    "\n<p>Additional info from the Editor-in-charge: </p><br/>"
                )
                email_text_html += cls.email_response
            email_text += (
                "\n\nThe text entries of your Report: "
                + "\n\nStrengths: \n"
                + cls.report.strengths
                + "\n\nWeaknesses: \n"
                + cls.report.weaknesses
                + "\n\nReport: \n"
                + cls.report.report
                + "\n\nRequested changes: \n"
                + cls.report.requested_changes
                + "\n\nRemarks for Editors: \n"
                + cls.report.remarks_for_editors
            )
            email_text_html += (
                "\n<p>The text entries of your Report: </p>"
                "\n<strong>Strengths</strong>: <br/><p>{{ strengths|linebreaks }}</p>"
                "\n<strong>Weaknesses</strong>: <br/><p>{{ weaknesses|linebreaks }}</p>"
                "\n<strong>Report</strong>: <br/><p>{{ report|linebreaks }}</p>"
                "\n<strong>Requested changes</strong>: <br/><p>{{ requested_changes|linebreaks }}</p>"
                "\n<strong>Remarks for Editors</strong>: <br/><p>{{ remarks_for_editors|linebreaks }}</p>"
            )
        email_context = {
            "ref_title": cls.report.author.profile.get_title_display(),
            "ref_last_name": cls.report.author.user.last_name,
            "sub_title": cls.report.submission.title,
            "author_list": cls.report.submission.author_list,
            "identifier_w_vn_nr": cls.report.submission.preprint.identifier_w_vn_nr,
            "strengths": cls.report.strengths,
            "weaknesses": cls.report.weaknesses,
            "report": cls.report.report,
            "requested_changes": cls.report.requested_changes,
            "remarks_for_editors": cls.report.remarks_for_editors,
        }
        if cls.report.status in [
            STATUS_UNCLEAR,
            STATUS_INCORRECT,
            STATUS_NOT_USEFUL,
            STATUS_NOT_ACADEMIC,
        ]:
            email_context["refusal_reason"] = cls.report.get_status_display()
        email_text_html += "<br/>" + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(Context(email_context))
        emailmessage = EmailMultiAlternatives(
            "SciPost: Report acknowledgement",
            email_text,
            f"SciPost Refereeing <refereeing@{domain}>",
            [cls.report.author.user.email],
            bcc=[
                cls.report.submission.editor_in_charge.user.email,
                f"refereeing@{domain}",
            ],
            reply_to=[f"refereeing@{domain}"],
        )
        emailmessage.attach_alternative(html_version, "text/html")
        emailmessage.send(fail_silently=False)

    @classmethod
    def send_author_report_received_email(cls):
        """Requires loading 'report' attribute."""
        email_text = (
            "Dear "
            + cls.report.submission.submitted_by.profile.get_title_display()
            + " "
            + cls.report.submission.submitted_by.user.last_name
            + ", \n\nA Report has been posted on your recent Submission to SciPost,\n\n"
            + cls.report.submission.title
            + " by "
            + cls.report.submission.author_list
            + "."
            "\n\nYou can view it at the Submission Page "
            f"https://{domain}/submission/"
            + cls.report.submission.preprint.identifier_w_vn_nr
            + "."
            "\n\nWe remind you that you can provide an author reply "
            "(only if you wish, to clarify points raised "
            "by the report) directly from this Submission Page. "
            "Any modification to your manuscript "
            "should await the Recommendation from the Editor-in-charge."
            "\n\nWe thank you very much for your contribution."
            "\n\nSincerely," + "\n\nThe SciPost Team."
        )
        email_text_html = (
            "<p>Dear {{ auth_title }} {{ auth_last_name }},</p>"
            "<p>A Report has been posted on your recent Submission to SciPost,</p>"
            "<p>{{ sub_title }}</p>\n<p>by {{ author_list }}.</p>"
            "\n<p>You can view it at the "
            f'<a href="https://{domain}' + '/submission/{{ identifier_w_vn_nr }}">'
            "Submission's page</a>.</p>"
            "<p>We remind you that you can provide an author reply "
            "(only if you wish, to clarify points raised "
            "by the report) directly from this Submission Page. "
            "Any modification to your manuscript "
            "should await the Recommendation from the Editor-in-charge.</p>"
            "\n<p>We thank you very much for your contribution.</p>"
            "<p>Sincerely,</p>"
            "<p>The SciPost Team.</p>"
        )
        email_context = {
            "auth_title": cls.report.submission.submitted_by.profile.get_title_display(),
            "auth_last_name": cls.report.submission.submitted_by.user.last_name,
            "sub_title": cls.report.submission.title,
            "author_list": cls.report.submission.author_list,
            "identifier_w_vn_nr": cls.report.submission.preprint.identifier_w_vn_nr,
        }
        email_text_html += "<br/>" + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(Context(email_context))
        emailmessage = EmailMultiAlternatives(
            "SciPost: Report received on your Submission",
            email_text,
            f"SciPost Editorial Admin <submissions@{domain}>",
            [cls.report.submission.submitted_by.user.email],
            bcc=[f"submissions@{domain}"],
            reply_to=[f"submissions@{domain}"],
        )
        emailmessage.attach_alternative(html_version, "text/html")
        emailmessage.send(fail_silently=False)

    @classmethod
    def send_communication_email(cls):
        """
        After an EditorialCommunication has been created and saved,
        this method sends emails to the relevant people.
        Requires loading 'communication' attribute.
        """
        recipient_email = []
        bcc_emails = []

        communication: "EditorialCommunication | None" = getattr(
            cls, "communication", None
        )
        if communication is None:
            raise ValueError("No communication attribute found. Please `.load()` it.")

        valid_comtypes = [comtype[0] for comtype in ED_COMM_CHOICES]

        # Referee to Author communication is strictly forbidden
        valid_comtypes.remove("RtoA")
        valid_comtypes.remove("AtoR")

        if communication.comtype not in valid_comtypes:
            raise ValueError(
                f"Invalid comtype {communication.comtype}. "
                f"Valid comtypes are {valid_comtypes}."
            )

        # BCC all non-edadmin communications to the Editorial Administrator
        if communication.recipient_letter != "S":
            bcc_emails.append(f"submissions@{domain}")

        # BCC all editor-authored communications to the Editor-in-charge
        if communication.author_letter == "E":
            bcc_emails.append(communication.author_email)

        # Further action page for Editor and Editorial Administrator
        if communication.recipient_letter in ["E", "S"]:  # _toS and _toE
            editorial_page_url = absolute_reverse(
                "submissions:editorial_page",
                args=[communication.submission.preprint.identifier_w_vn_nr],
            )
            further_action = (
                f"You can take follow-up actions from {editorial_page_url}."
            )
        # Further action page for Author and Referee
        elif communication.recipient_letter in ["R", "A"]:  # _toA and _toR
            preprint_identifier = communication.submission.preprint.identifier_w_vn_nr
            reverse_communication_url = absolute_reverse(
                "submissions:communication",
                args=[
                    preprint_identifier,
                    communication.recipient_letter + "to" + communication.author_letter,
                    # Reverse the communication direction, e.g. EtoA -> AtoE
                ],
            )
            submission_page_url = absolute_reverse(
                "submissions:submission",
                args=[preprint_identifier],
            )

            # Create a dictionary mapping author letters to author kinds
            author_kinds = dict(zip(*zip(*ED_COMM_PARTIES)))
            author_kind = author_kinds.get(communication.author_letter)
            further_action = (
                f"To reply to the {author_kind}, please visit {reverse_communication_url}. "
                f"You can find all previous communications between you and the {author_kind}, as well as other communications tools, "
                f"on the submission page at {submission_page_url} (login needed)."
            )

        email_text = (
            f"Dear {communication.recipient_name},\n\n"
            f"Please find here a communication ({communication.get_comtype_display()}) concerning Submission:\n\n"
            f"{communication.submission.title}\nby {communication.submission.author_list}.\n"
            f"(https://{domain}{communication.submission.get_absolute_url()})\n\n"
            "Text of the communication:\n"
            "------------------------------------------\n"
            f"{communication.text}\n"
            "------------------------------------------\n\n"
            f"{further_action}\n\n"
            "We thank you very much for your contribution.\n\n"
            "Sincerely,\n"
            "The SciPost Team."
        )

        emailmessage = EmailMessage(
            f"SciPost: communication ({communication.get_comtype_display()})",
            email_text,
            f"SciPost Editorial Admin <submissions@{domain}>",
            [communication.recipient_email],
            bcc_emails,
            reply_to=[f"submissions@{domain}"],
        )
        emailmessage.send(fail_silently=False)

    @classmethod
    def send_author_revision_requested_email(cls):
        """Requires loading 'submission' and 'recommendation' attributes."""

        from submissions.models import EICRecommendation, Submission

        recommendation = getattr(cls, "recommendation", None)
        submission = getattr(cls, "submission", None)

        if not isinstance(recommendation, EICRecommendation):
            raise ValueError("No recommendation attribute found. Please `.load()` it.")
        if not isinstance(submission, Submission):
            raise ValueError("No submission attribute found. Please `.load()` it.")

        match recommendation.recommendation:
            case -1:  # Minor revision
                revision_type = "minor"
            case -2:  # Major revision
                revision_type = "major"
            case _:  # Unknown revision type
                raise ValueError("Unknown revision type")

        email_text = (
            "Dear {auth_title} {auth_last_name},"
            "\n\n"
            "The Editor-in-charge of your recent Submission to {original_journal_name},\n"
            "{sub_title}\nby {author_list},\n"
            "has formulated an Editorial Recommendation, asking for a {revision_type} revision."
            "\n\n"
            + (
                "Moreover, the Editor-in-charge recommends you to submit your modified manuscript "
                "to {recommendation_journal_name} instead. You can find more information on {recommendation_journal_name}, "
                "including its acceptance criteria, at https://{domain}/{recommendation_journal_doi}/about."
                if recommendation.for_journal
                and recommendation.for_journal != submission.submitted_to
                else ""
            )
            + "You can view the full recommendation at the Submission's Page "
            "https://{domain}/submission/{identifier_w_vn_nr} "
            "together with possible Remarks for authors and Requested changes."
            "Note that the recommendation is viewable only by "
            "the registered authors of the submission."
            "\n\n"
            "To resubmit your paper, please first update the version "
            "on the preprint server you used to submit the manuscript (e.g. arXiv); "
            "after appearance, go to the submission page "
            "https://{domain}/submissions/submit_manuscript and fill in the forms. "
            "Your submission will be automatically recognized as a resubmission. "
            "We remind you that you can reply to the referee report(s) "
            'directly from this Submission Page, using the "Reply to the above Report" link below each report.'
            "\n\n"
            + (
                "Remarks for authors from the Editor-in-charge:\n"
                "{remarks_for_authors}"
                "\n\n"
                if recommendation.remarks_for_authors
                else ""
            )
            + (
                "Requested changes:\n" "{requested_changes}" "\n\n"
                if recommendation.requested_changes
                else ""
            )
            + "We thank you very much for your contribution."
            "\n\nSincerely," + "\nThe SciPost Team."
        )
        email_text_html = (
            "<p>Dear {{ auth_title }} {{ auth_last_name }},</p>"
            "<p>The Editor-in-charge of your recent Submission to {{ original_journal_name }},</p>"
            "<p>{{ sub_title }}\nby {{ author_list }},</p>"
            "\n<p>has formulated an Editorial Recommendation, asking for a {{ revision_type }} revision.</p>"
            + (
                "<p>Moreover, the Editor-in-charge recommends you to submit your modified manuscript "
                "to <strong>{{ recommendation_journal_name }}</strong> instead. "
                "You can find more information on {{ recommendation_journal_name }}, "
                "including its acceptance criteria, at its "
                '<a href="https://{{ domain }}/{{ recommendation_journal_doi }}/about">about</a> page.</p>'
                if recommendation.for_journal
                and recommendation.for_journal != submission.submitted_to
                else ""
            )
            + "\n<p>You can view the full recommendation at the "
            '<a href="https://{{ domain }}/submission/'
            "{{ identifier_w_vn_nr }}\">Submission's Page</a>. "
            "Note that the recommendation is viewable only by "
            "the registered authors of the submission.</p>"
            "<p>To resubmit your paper, please first update the version "
            "on the preprint server you used to submit the manuscript (e.g. arXiv); "
            "after appearance, go to the "
            '<a href="https://{{ domain }}/submissions/submit_manuscript">'
            "submission page</a> and fill the forms in. "
            "Your submission will be automatically recognized as a resubmission.</p>"
            "<p>We remind you that you can reply to the referee report(s) "
            'directly from this Submission Page, using the "Reply to the above Report" link below each report.</p>'
            + (
                "<p>Remarks for authors from the Editor-in-charge:</p>"
                "<p>{{ remarks_for_authors }}</p>"
                if recommendation.remarks_for_authors
                else ""
            )
            + (
                "<p>Requested changes:</p>" "<p>{{ requested_changes }}</p>"
                if recommendation.requested_changes
                else ""
            )
            + "\n<p>We thank you very much for your contribution.</p>"
            "<p>Sincerely,\nThe SciPost Team.</p>"
        )
        email_context = {
            "auth_title": submission.submitted_by.profile.get_title_display(),
            "auth_last_name": submission.submitted_by.user.last_name,
            "sub_title": submission.title,
            "author_list": submission.author_list,
            "identifier_w_vn_nr": submission.preprint.identifier_w_vn_nr,
            "original_journal_name": submission.submitted_to.name,
            "revision_type": revision_type,
            "recommendation_journal_name": recommendation.for_journal.name,
            "recommendation_journal_doi": recommendation.for_journal.doi_label,
            "remarks_for_authors": recommendation.remarks_for_authors,
            "requested_changes": recommendation.requested_changes,
            "domain": domain,
        }
        email_text_html += "<br/>" + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(Context(email_context))
        emailmessage = EmailMultiAlternatives(
            "SciPost: revision requested",
            email_text.format(**email_context),
            f"SciPost Editorial Admin <submissions@{domain}>",
            [submission.submitted_by.user.email],
            bcc=[submission.editor_in_charge.user.email, f"submissions@{domain}"],
            reply_to=[f"submissions@{domain}"],
        )
        emailmessage.attach_alternative(html_version, "text/html")
        emailmessage.send(fail_silently=False)

    @classmethod
    def send_author_College_decision_email(cls):
        """Requires loading 'submission' and 'recommendation' attributes."""
        email_text = (
            "Dear "
            + cls.submission.submitted_by.profile.get_title_display()
            + " "
            + cls.submission.submitted_by.user.last_name
            + ", \n\nThe Editorial College of SciPost has taken a decision "
            "regarding your recent Submission,\n\n"
            + cls.submission.title
            + " by "
            + cls.submission.author_list
            + ".\n\n"
        )
        email_text_html = (
            "<p>Dear {{ auth_title }} {{ auth_last_name }},</p>"
            "<p>The Editorial College of SciPost has taken a decision "
            "regarding your recent Submission,</p>"
            "<p>{{ sub_title }}</p>\n<p>by {{ author_list }}.</p>"
        )
        if (
            cls.recommendation.recommendation == 1
            or cls.recommendation.recommendation == 2
            or cls.recommendation.recommendation == 3
        ):
            email_text += (
                "We are pleased to inform you that your Submission "
                "has been accepted for publication in "
                + cls.recommendation.get_for_journal_display()
            )  # submission.submitted_to)
            email_text_html += (
                "<p>We are pleased to inform you that your Submission "
                "has been accepted for publication in <strong>{{ journal }}</strong>"
            )
            if (
                cls.recommendation.recommendation == 1 and False
            ):  # Temporary deactivation of Select
                email_text += (
                    ", with a promotion to Select. We warmly congratulate you "
                    "on this achievement, which is reserved to papers deemed in "
                    "the top ten percent of papers we publish."
                )
                email_text_html += (
                    ", with a promotion to <strong>Select</strong>. We warmly congratulate you "
                    "on this achievement, which is reserved to papers deemed in "
                    "the top ten percent of papers we publish.</p>"
                )
            else:
                email_text += "."
                email_text_html += "."
            email_text += (
                "\n\nYour manuscript will now be taken charge of by our "
                "production team, who will soon send you proofs "
                "to check before final publication."
            )
            email_text_html += (
                "\n<p>Your manuscript will now be taken charge of by our "
                "production team, who will soon send you proofs "
                "to check before final publication.</p>"
            )

        elif cls.recommendation.recommendation == -3:
            email_text += (
                "We are sorry to inform you that your Submission "
                "has not been accepted for publication. "
                "\n\nYou can view more details at the Submission Page "
                f"https://{domain}/submission/"
                + cls.submission.preprint.identifier_w_vn_nr
                + ". "
                "Note that these details are viewable only by "
                "the registered authors of the submission."
                "\n\nThis Submission Page has now been removed "
                "from general public view; if you wish, you can email us and "
                "request to make it publicly visible again."
            )
            email_text_html += (
                "<p>We are sorry to inform you that your Submission "
                "has not been accepted for publication.</p>"
                "\n<p>You can view more details at the "
                f'<a href="https://{domain}/submission/'
                "{{ identifier_w_vn_nr }}\">Submission's Page</a>. "
                "Note that these details are viewable only by "
                "the registered authors of the submission.</p>"
                "<p>This Submission Page has now been removed "
                "from general public view; if you wish, you can email us and "
                "request to make it publicly visible again.</p>"
            )
        email_text += (
            "\n\nWe thank you very much for your contribution."
            "\n\nSincerely,"
            "\n\nThe SciPost Team."
        )
        email_text_html += (
            "\n<p>We thank you very much for your contribution.</p>"
            "<p>Sincerely,</p>"
            "<p>The SciPost Team.</p>"
        )
        email_context = {
            "auth_title": cls.submission.submitted_by.profile.get_title_display(),
            "auth_last_name": cls.submission.submitted_by.user.last_name,
            "sub_title": cls.submission.title,
            "author_list": cls.submission.author_list,
            "identifier_w_vn_nr": cls.submission.preprint.identifier_w_vn_nr,
            "journal": cls.recommendation.get_for_journal_display(),
        }
        email_text_html += "<br/>" + EMAIL_FOOTER
        html_template = Template(email_text_html)
        html_version = html_template.render(Context(email_context))
        emailmessage = EmailMultiAlternatives(
            "SciPost: College decision",
            email_text,
            f"SciPost Editorial Admin <submissions@{domain}>",
            [cls.submission.submitted_by.user.email],
            bcc=[cls.submission.editor_in_charge.user.email, f"submissions@{domain}"],
            reply_to=[f"submissions@{domain}"],
        )
        emailmessage.attach_alternative(html_version, "text/html")
        emailmessage.send(fail_silently=False)

    @classmethod
    def send_fellow_voting_reminder_email(cls):
        """
        Sends an email reminding a Fellow of their voting duties regarding a submission.
        Requires loading 'fellow' a `Fellow` instance, and 'recommendation' an `EICRecommendation` instance.
        """
        cls.mail_sender = f"edadmin@{domain}"

        cls._send_mail(
            cls,
            "email_remind_fellow_voting_duties",
            [cls._context["fellow"].user.email],
            "SciPost: voting duties reminder",
        )


def remove_file_metadata(
    file_path: str,
    keywords: list[str],
    all_but_given: bool = False,
    blocking: bool = False,
):
    """
    Remove metadata from a file using exiftool.
    - `file_path`: path to the file to be cleaned
    - `keywords`: list of keywords to be removed if `all_but_given` is False, or to be kept if `all_but_given` is True
    - `blocking`: whether to block the main thread until the subprocess has finished
    """

    # launch subprocess to remove metadata from file, e.g.
    # exiftool -overwrite_original -all= -tagsFromFile @ -“Title” -“Page Count” filename.pdf
    p = subprocess.Popen(
        [
            "exiftool",
            "-overwrite_original",
            *(["-all=", "-tagsFromFile", "@"] if all_but_given else []),
            *[f"-{keyword}" for keyword in keywords],
            file_path,
        ],
    )

    if blocking:
        p.wait()


def linearize_pdf(file_path: str, blocking: bool = False):
    """
    Linearize a PDF file using qpdf.
    - `file_path`: path to the file to be linearized
    - `blocking`: whether to block the main thread until the subprocess has finished
    """
    p = subprocess.Popen(["qpdf", "--linearize", file_path, "--replace-input"])

    if blocking:
        p.wait()


def clean_pdf(file_path: str):
    """
    Clean the PDF file, removing metadata and linearizing it.
    """

    # TODO Do not fail silently, but raise an exception
    if not file_path.endswith(".pdf"):
        # raise ValueError("File must be a PDF")
        return

    if not os.path.isfile(file_path):
        # raise FileNotFoundError(f"File {file_path} does not exist")
        return

    # backup original file
    subprocess.run(["cp", file_path, file_path + ".bak"])

    try:
        remove_file_metadata(
            file_path,
            [
                "title",
                "producer",
                "creator",
                "createdate",
                "modifydate",
            ],
            all_but_given=True,
            blocking=True,
        )

        linearize_pdf(file_path)

    except subprocess.CalledProcessError as e:
        print(f"Error while processing file {file_path}: {e}")
        # restore original file
        subprocess.run(["rm", file_path])
        subprocess.run(["mv", file_path + ".bak", file_path])

    # Delete intermediate files
    subprocess.run(["rm", file_path + ".~qpdf-orig"])

    # TODO Remove the backup file after we are sure it is not needed anymore
