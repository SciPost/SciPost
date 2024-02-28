__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin


from .models import Category, BlogPost


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}




@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}


