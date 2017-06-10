from django import forms
from django.conf import settings

from mailchimp3 import MailChimp

from .constants import MAIL_LIST_STATUS_ACTIVE, MAIL_LIST_STATUS_DEACTIVATED
from .models import MailchimpList


class MailchimpUpdateForm(forms.Form):
    """
    This form does the synchronizing of mailing lists in the database.
    """
    def __init__(self):
        self.client = MailChimp(settings.MAILCHIMP_API_USER, settings.MAILCHIMP_API_KEY)
        self.lists = MailchimpList.objects.active()

    def sync(self):
        # Deactivate all mailing lists by default
        MailchimpList.objects.active().update(status=MAIL_LIST_STATUS_DEACTIVATED)

        # Connect the client to Mailchimp API
        client = MailChimp(settings.MAILCHIMP_API_USER, settings.MAILCHIMP_API_KEY)
        response = client.lists.all(get_all=True, fields="lists.name,lists.id")

        # Do the update for all Lists recieved
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
        return _list.update_members()
