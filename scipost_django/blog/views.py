__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import render
from django.views.generic import DetailView

from .models import Category, BlogPost
from .forms import BlogPostSearchForm


def blog_index(request):
    categories = Category.objects.all()
    latest_posts = BlogPost.objects.all()[:5]
    form = BlogPostSearchForm(user=request.user)
    context = {
        "categories": categories,
        "latest_posts": latest_posts,
        "form": form,
    }
    return render(request, "blog/blog_index.html", context)


def _hx_posts(request):
    form = BlogPostSearchForm(request.POST or None, user=request.user)
    posts = form.search()
    paginator = Paginator(posts, 16)
    page_nr = request.GET.get("page")
    page_obj = paginator.get_page(page_nr)
    count = paginator.count
    start_index = page_obj.start_index
    context = {
        "posts": posts,
        "count": count,
        "page_obj": page_obj,
        "start_index": start_index,
    }
    return render(request, "blog/_hx_posts.html", context)


class BlogPostDetailView(DetailView):
    model = BlogPost

    def get_object(self):
        blogpost = super().get_object()
        if blogpost.status != blogpost.PUBLISHED and not self.request.user.has_perm(
            "blog.change_blogpost"
        ):
            raise Http404
        return blogpost
