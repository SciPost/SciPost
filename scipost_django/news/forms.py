__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from .models import NewsCollection, NewsItem, NewsCollectionNewsItemsTable


class NewsCollectionForm(forms.ModelForm):
    class Meta:
        model = NewsCollection
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


class NewsCollectionNewsItemsTableForm(forms.ModelForm):
    class Meta:
        model = NewsCollectionNewsItemsTable
        fields = ["newsitem"]


class NewsCollectionNewsItemsTableFormSet(forms.BaseModelFormSet):
    def save(self, *args, **kwargs):
        objects = super().save(*args, **kwargs)
        for form in self.ordered_forms:
            form.instance.order = form.cleaned_data["ORDER"]
            form.instance.save()
        return objects


NewsCollectionNewsItemsOrderingFormSet = forms.modelformset_factory(
    NewsCollectionNewsItemsTable,
    fields=(),
    can_order=True,
    extra=0,
    formset=NewsCollectionNewsItemsTableFormSet,
)
