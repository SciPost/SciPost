__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms
from django.db.models import Q

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field
from crispy_bootstrap5.bootstrap5 import FloatingField

from .models import Category, BlogPost


class BlogPostSearchForm(forms.Form):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
    )
    q = forms.CharField(
        max_length=32,
        label="Search (title, body, author)",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(Field("category"), css_class="col-lg-4"),
                Div(FloatingField("q", autocomplete="off"), css_class="col-lg-8"),
                css_class="row",
            ),
            Field("slug", type="hidden"),
        )

    def search_results(self):
        posts = BlogPost.objects.all()
        if self.cleaned_data["category"]:
            posts = posts.filter(categories=self.cleaned_data["category"])
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
            posts = posts.filter(query).distinct()
        if not self.user.has_perm("blog.change_blogpost"):
            posts = posts.published()
        return posts
