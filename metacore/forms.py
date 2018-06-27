from django import forms

import logging
import re

from .models import Citable, CitableWithDOI

logger = logging.getLogger(__name__)

# Move to application-wide constant if used more
# Taken from https://www.crossref.org/blog/dois-and-matching-regular-expressions
doi_regex = re.compile(r'^10.\d{4,9}\/[-._;()/:A-Z0-9]+$', re.IGNORECASE)

class CitableSearchForm(forms.Form):
    omni      = forms.CharField(max_length=100, required=False, label="Authors / title (text search)")
    author    = forms.CharField(max_length=100, required=False, label="Author(s)")
    title     = forms.CharField(max_length=100, required=False)
    publisher = forms.CharField(max_length=100, required=False)
    journal   = forms.CharField(max_length=100, required=False)
    doi       = forms.CharField(max_length=100, required=False)

    def search_results(self):
        """Return all Citable objects according to search"""
        query_params = {
            'title__icontains':                     self.cleaned_data.get('title', ''),
            'authors__icontains':                   self.cleaned_data.get('author', ''),
            'publisher__icontains':                 self.cleaned_data.get('publisher', ''),
            'metadata__container-title__icontains': self.cleaned_data.get('journal', ''),
        }

        # DOI's are always lower case in the metacore app
        doi_query = self.cleaned_data.get('doi', '').lower()
        if doi_regex.match(doi_query):
            # Use index (fast)
            print('Using doi index')
            query_params['doi'] = doi_query
        else:
            # Partial match (can't use index)
            print('Not using doi index')
            query_params['doi__icontains'] = doi_query

        if self.cleaned_data.get('omni', False):
            """If a text index is present, search using the authors/title box is enables"""
            return Citable.objects.simple().filter(**query_params).omni_search(self.cleaned_data.get('omni'), 'and')
        else:
            if self.is_empty():
                return None

            return Citable.objects.simple().filter(**query_params)

    def is_empty(self):
        form_empty = True
        for field_value in self.cleaned_data.values():
            if field_value is not None and field_value != '':
                form_empty = False
                break

        if form_empty:
            return None
