from django.conf.urls import include, url

from django.views.generic import TemplateView

#from . import views
from journals import views as journals_views

urlpatterns = [
    # Journals
    url(r'^$', journals_views.journals, name='journals'),
    url(r'^journals_terms_and_conditions$', 
        TemplateView.as_view(template_name='journals/journals_terms_and_conditions.html'), 
        name='journals_terms_and_conditions'),
    # SciPost Physics
    url(r'^scipost_physics$', 
        journals_views.scipost_physics, 
        name='scipost_physics'),
    url(r'^scipost_physics/accepted$', 
        journals_views.scipost_physics_accepted, 
        name='scipost_physics_accepted'),
    url(r'^scipost_physics/info_for_authors$', 
        journals_views.scipost_physics_info_for_authors, 
        name='scipost_physics_info_for_authors'),
    url(r'^scipost_physics/about$', 
        journals_views.scipost_physics_about, 
        name='scipost_physics_about'),

    # Editorial and Administrative Workflow
    url(r'^publish_accepted_submission$', 
        journals_views.publish_accepted_submission, 
        name='publish_accepted_submission'),
]
