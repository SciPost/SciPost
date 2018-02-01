from django import forms

from .models import Citable, CitableWithDOI


class CitableSearchForm(forms.Form):
    author = forms.CharField(max_length=100, required=False, label="Author(s)")
    title = forms.CharField(max_length=100, required=False)
    publisher = forms.CharField(max_length=100, required=False)

    def search_results(self):
        """Return all Citable objects according to search"""
        return Citable.objects.simple().filter(
            title__icontains=self.cleaned_data.get('title', ''),
            authors__icontains=self.cleaned_data.get('author', ''),
            publisher__icontains=self.cleaned_data.get('publisher', ''),
        )

