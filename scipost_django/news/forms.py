__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from .models import NewsLetter, NewsItem, NewsLetterNewsItemsTable


class NewsLetterForm(forms.ModelForm):
    class Meta:
        model = NewsLetter
        fields = ["date", "intro", "closing", "published"]


class NewsItemForm(forms.ModelForm):
    class Meta:
        model = NewsItem
        fields = [
            "date",
            "headline",
            "blurb_short",
            "blurb",
            "image",
            "css_class",
            "followup_link",
            "followup_link_text",
            "published",
            "on_homepage",
        ]


class NewsLetterNewsItemsTableForm(forms.ModelForm):
    class Meta:
        model = NewsLetterNewsItemsTable
        fields = ["newsitem"]


class NewsLetterNewsItemsTableFormSet(forms.BaseModelFormSet):
    def save(self, *args, **kwargs):
        objects = super().save(*args, **kwargs)
        for form in self.ordered_forms:
            form.instance.order = form.cleaned_data["ORDER"]
            form.instance.save()
        return objects


NewsLetterNewsItemsOrderingFormSet = forms.modelformset_factory(
    NewsLetterNewsItemsTable,
    fields=(),
    can_order=True,
    extra=0,
    formset=NewsLetterNewsItemsTableFormSet,
)
