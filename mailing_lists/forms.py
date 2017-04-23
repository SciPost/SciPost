from django import forms
from django.conf import settings

from mailchimp3 import MailChimp

from .constants import MAIL_LIST_STATUS_ACTIVE, MAIL_LIST_STATUS_DEACTIVATED
from .models import MailchimpList

from scipost.models import Contributor


class MailchimpUpdateForm(forms.Form):
    """
    This form does the synchronizing of mailing lists in the database.
    """
    def __init__(self):
        self.client = MailChimp(settings.MAILCHIMP_API_USER, settings.MAILCHIMP_API_KEY)
        self.lists = MailchimpList.objects.active()

    def sync(self):
        response = self.client.lists.all(get_all=True, fields="lists.name,lists.id")

        # Deactivate all mailing lists by default
        self.lists.update(status=MAIL_LIST_STATUS_DEACTIVATED)
        count = 0
        while response['lists']:
            _list = response['lists'].pop()
            chimplist, created = MailchimpList.objects.get_or_create(mailchimp_list_id=_list['id'])
            chimplist.name = _list['name']
            chimplist.status = MAIL_LIST_STATUS_ACTIVE
            chimplist.save()
            count += 1
        return count

    def sync_members(self, _list):
        contributors = (Contributor.objects.active()
                        .filter(accepts_SciPost_emails=True,
                                user__groups__in=_list.allowed_groups.all()))
        for contributor in contributors:
            payload = {
                'email_address': contributor.user.email,
                'status': 'subscribed',
                'merge_fields': {
                    'FNAME': contributor.user.first_name,
                    'LNAME': contributor.user.last_name,
                },
            }
            try:
                self.client.lists.members.create(_list.mailchimp_list_id, payload)
            except:
                continue
        return len(contributors)
