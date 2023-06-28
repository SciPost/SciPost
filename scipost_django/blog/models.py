__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf import settings
from django.db import models
from django.urls import reverse

from .managers import BlogPostQuerySet


class Category(models.Model):
    title = models.CharField(max_length=64)
    slug = models.SlugField(unique=True)
    description = models.TextField(default="(insert description)")

    class Meta:
        ordering = ["title"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            "blog:category_detail",
            kwargs={
                "slug": self.slug,
            },
        )


class BlogPost(models.Model):
    DRAFT = "draft"
    PUBLISHED = "published"
    DELISTED = "delisted"
    STATUS_CHOICES = (
        (DRAFT, "Draft"),
        (PUBLISHED, "Published"),
        (DELISTED, "Delisted"),
    )
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
    )
    title = models.CharField(max_length=256)
    slug = models.SlugField(unique=True)
    categories = models.ManyToManyField(Category, blank=True)
    blurb = models.TextField()
    blurb_image = models.ImageField(upload_to="blog/posts/%Y/%m", blank=True)
    blurb_image_caption = models.TextField(blank=True)
    body = models.TextField()
    date_posted = models.DateTimeField()
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    objects = BlogPostQuerySet.as_manager()

    class Meta:
        ordering = ["-date_posted"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        kwargs = {
            "slug": self.slug,
            "year": "%04d" % self.date_posted.year,
            "month": "%02d" % self.date_posted.month,
            "day": "%02d" % self.date_posted.day,
        }
        return reverse("blog:blogpost_detail", kwargs=kwargs)
