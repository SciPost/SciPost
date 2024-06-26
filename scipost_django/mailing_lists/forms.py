__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from typing import Any
from django import forms
from django.conf import settings

from mailchimp3 import MailChimp

from crispy_forms.helper import FormHelper, Layout
from crispy_forms.layout import Div, Submit
from crispy_bootstrap5.bootstrap5 import FloatingField, Field

from .constants import MAIL_LIST_STATUS_ACTIVE, MAIL_LIST_STATUS_DEACTIVATED
from .models import MailchimpList, MailingList, Newsletter


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
        while response["lists"]:
            _list = response["lists"].pop()
            chimplist, created = MailchimpList.objects.get_or_create(
                mailchimp_list_id=_list["id"]
            )
            chimplist.name = _list["name"]
            chimplist.status = MAIL_LIST_STATUS_ACTIVE
            chimplist.save()
            count += 1
        return count

    def sync_mailchimp_members(self, _list):
        return _list.update_members()


class MailingListForm(forms.ModelForm):
    class Meta:
        model = MailingList

        fields = ["name", "slug", "is_opt_in"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Div(FloatingField("name"), css_class="col"),
                Div(FloatingField("slug"), css_class="col"),
                Div(Field("is_opt_in"), Submit("submit", "Save"), css_class="col-auto"),
                css_class="row",
            )
        )


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = Newsletter

        fields = ["title", "content"]

    content = forms.CharField(widget=forms.Textarea(attrs={"class": "h-100"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(FloatingField("title"), css_class="col-12"),
            Div(
                Field("content", wrapper_class="h-100 d-flex flex-column"),
                css_class="col-6",
            ),
        )

    def clean_title(self) -> str:
        title = self.cleaned_data.get("title")

        if title is None:
            self.add_error("title", "Title is required")

        title = title.strip()
        if len(title) == 0:
            self.add_error("title", "Title must not be empty")

        return title

    def clean_content(self) -> str:
        content = self.cleaned_data.get("content")

        if content is None:
            self.add_error("content", "Content is required")

        content = content.strip()
        if len(content) == 0:
            self.add_error("content", "Content must not be empty")

        return content


class NewsletterUploadMediaForm(forms.Form):
    """
    Form to upload media for a newsletter. It stores the media in a folder related to the newsletter.
    The media is not stored in any model but directly on the filesystem, so it can be accessed by the newsletter.
    """

    media_file = forms.FileField(required=False)

    def __init__(self, *args, **kwargs):
        self.newsletter = kwargs.pop("newsletter")
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.layout = Layout(
            Div(Field("media_file"), css_class="col"),
            Div(Submit("submit", "Upload"), css_class="col-auto mt-auto"),
        )

    def clean_media_file(self) -> Any:
        media_file = self.cleaned_data.get("media_file")

        if media_file is None:
            self.add_error("media_file", "Media file is required")

        return media_file

    def save(self):
        media_file = self.cleaned_data.get("media_file")
        media_folder = settings.MEDIA_ROOT + self.newsletter.get_media_folder()

        with open(f"{media_folder}/{media_file.name}", "wb+") as destination:
            for chunk in media_file.chunks():
                destination.write(chunk)

        return media_file.name
