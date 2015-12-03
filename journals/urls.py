from django.conf.urls import include, url

#from . import views
from journals import views as journals_views

urlpatterns = [
    # Journals
    url(r'^$', journals_views.journals, name='journals'),
]
