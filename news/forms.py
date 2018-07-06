__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from .models import NewsLetter, NewsItem, NewsLetterNewsItemsTable


class NewsLetterForm(forms.ModelForm):

    class Meta:
        model = NewsLetter
        fields = ['date', 'intro', 'closing', 'published']


class NewsItemForm(forms.ModelForm):

    class Meta:
        model = NewsItem
        fields = ['date', 'headline', 'blurb_short', 'blurb',
                  'image', 'css_class',
                  'followup_link', 'followup_link_text',
                  'published', 'on_homepage']


class NewsLetterNewsItemsTableForm(forms.ModelForm):

    class Meta:
        model = NewsLetterNewsItemsTable
        fields = ['newsitem']
