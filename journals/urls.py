from django.conf.urls import include, url

from django.views.generic import TemplateView

#from . import views
from journals import views as journals_views

urlpatterns = [
    # Journals
    url(r'^$', journals_views.journals, name='journals'),
    url(r'^journals_terms_and_conditions$', TemplateView.as_view(template_name='journals/journals_terms_and_conditions.html'), name='journals_terms_and_conditions'),
]
