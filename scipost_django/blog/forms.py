__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms
from django.db.models import Q, QuerySet

from crispy_forms.layout import Layout, Div, Field
from crispy_bootstrap5.bootstrap5 import FloatingField

from common.forms import CrispyFormMixin, SearchForm

from .models import Category, BlogPost


class BlogPostSearchForm(CrispyFormMixin, SearchForm[BlogPost]):
    model = BlogPost

    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
    )
    q = forms.CharField(
        max_length=32,
        label="Search (title, body, author)",
        required=False,
    )

    def get_form_layout(self) -> Layout:
        return Layout(
            Div(
                Div(Field("category"), css_class="col-lg-4"),
                Div(FloatingField("q", autocomplete="off"), css_class="col-lg-8"),
                css_class="row",
            ),
            Field("slug", type="hidden"),
        )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def filter_queryset(self, queryset: "QuerySet[BlogPost]"):
        if self.cleaned_data["category"]:
            queryset = queryset.filter(categories=self.cleaned_data["category"])
        if self.cleaned_data["q"]:
            splitwords = self.cleaned_data["q"].replace(",", "").split(" ")
            query = Q()
            for word in splitwords:
                query = query & (
                    Q(title__icontains=word)
                    | Q(blurb__icontains=word)
                    | Q(body__icontains=word)
                    | Q(posted_by__first_name__icontains=word)
                    | Q(posted_by__last_name__icontains=word)
                )
            queryset = queryset.filter(query).distinct()
        if not self.user.has_perm("blog.change_blogpost"):
            queryset = queryset.published()
        return queryset
