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
        self.objects = MailchimpList.objects.active()

    def sync(self):
        response = self.client.lists.all(get_all=True, fields="lists.name,lists.id")

        # Deactivate all mailing lists by default
        self.objects.update(status=MAIL_LIST_STATUS_DEACTIVATED)
        count = 0
        while response['lists']:
            _list = response['lists'].pop()
            chimplist, created = MailchimpList.objects.get_or_create(mailchimp_list_id=_list['id'])
            chimplist.name = _list['name']
            chimplist.status = MAIL_LIST_STATUS_ACTIVE
            chimplist.save()
            count += 1
        return count
