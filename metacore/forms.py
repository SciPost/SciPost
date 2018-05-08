from django import forms

import logging

from .models import Citable, CitableWithDOI

logger = logging.getLogger(__name__)

class CitableSearchForm(forms.Form):
    omni = forms.CharField(max_length=100, required=False, label="Authors / title (text search)")
    author = forms.CharField(max_length=100, required=False, label="Author(s)")
    title = forms.CharField(max_length=100, required=False)
    publisher = forms.CharField(max_length=100, required=False)
    journal = forms.CharField(max_length=100, required=False)

    def search_results(self):
        """Return all Citable objects according to search"""
        if not self.cleaned_data.get('omni', False):
            if self.is_empty:
                return None

            return Citable.objects.simple().filter(
                title__icontains=self.cleaned_data.get('title', ''),
                authors__icontains=self.cleaned_data.get('author', ''),
                publisher__icontains=self.cleaned_data.get('publisher', ''),
                **{'metadata__container-title__icontains': self.cleaned_data.get('journal', '')},
            )
        else:

            """If a text index is present, search using the authors/title box is enables"""
            return Citable.objects.simple().filter(
                title__icontains=self.cleaned_data.get('title', ''),
                authors__icontains=self.cleaned_data.get('author', ''),
                publisher__icontains=self.cleaned_data.get('publisher', ''),
                **{'metadata__container-title__icontains': self.cleaned_data.get('journal', '')},
            ).omni_search(self.cleaned_data.get('omni'), 'and')

    def is_empty(self):
        form_empty = True
        for field_value in self.cleaned_data.values():
            if field_value is not None and field_value != '':
                form_empty = False
                break

        if form_empty:
            return None
