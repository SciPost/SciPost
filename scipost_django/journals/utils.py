__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.sites.models import Site
from django.core.mail import EmailMessage

from common.utils import BaseMailUtil


class JournalUtils(BaseMailUtil):
    mail_sender = "edadmin@%s" % Site.objects.get_current().domain
    mail_sender_title = "SciPost Editorial Admin"

    @classmethod
    def send_authors_paper_published_email(cls):
        """Requires loading 'publication' attribute."""
        domain = Site.objects.get_current().domain
        email_text = (
            "Dear "
            + cls.publication.accepted_submission.submitted_by.profile.get_title_display()
            + " "
            + cls.publication.accepted_submission.submitted_by.user.last_name
            + ", \n\nWe are happy to inform you that your Submission to SciPost,\n\n"
            + cls.publication.accepted_submission.title
            + " by "
            + cls.publication.accepted_submission.author_list
            + "\n\nhas been published online with reference "
            + cls.publication.citation
            + "."
            "\n\nThe publication page is located at the permanent link "
            "https://" + domain + "/" + cls.publication.doi_label + "."
            "\n\nThe permanent DOI for your publication is 10.21468/"
            + cls.publication.doi_label
            + "."
            "\n\nTo facilitate dissemination of your paper, we will also automatically "
            "update the arXiv Journal-ref with this information (this update usually "
            "takes place within one week; you do not need to take action)."
            "\n\nWe warmly congratulate you on this achievement and thank you "
            "for entrusting us with the task of publishing your research. "
            "\n\nSincerely," + "\n\nThe SciPost Team."
        )
        emailmessage = EmailMessage(
            "SciPost: paper published",
            email_text,
            "SciPost Editorial Admin <edadmin@%s>" % domain,
            [
                cls.publication.accepted_submission.submitted_by.user.email,
                "edadmin@%s" % domain,
            ],
            reply_to=["edadmin@%s" % domain],
        )
        emailmessage.send(fail_silently=False)

    @classmethod
    def email_report_made_citable(cls):
        """Requires loading 'report' attribute."""
        cls._send_mail(
            cls,
            "email_report_made_citable",
            [cls._context["report"].author.user.email],
            "Report made citable",
        )

    @classmethod
    def email_comment_made_citable(cls):
        """Requires loading 'comment' attribute."""
        cls._send_mail(
            cls,
            "email_comment_made_citable",
            [cls._context["comment"].author.user.email],
            "Comment made citable",
        )
