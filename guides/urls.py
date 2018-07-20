__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url
from django.views.generic import TemplateView

urlpatterns = [
    url(r'^$',
        TemplateView.as_view(template_name='guides/guides_index.html'),
        name='guides_index'),
    url(r'^editorial/submissions/submission_processing$',
        TemplateView.as_view(
            template_name='guides/editorial/submissions/submission_prescreening.html'),
        name='submission_prescreening'),
    url(r'^editorial/production/initial_production$',
        TemplateView.as_view(template_name='guides/editorial/production/initial_production.html'),
        name='initial_production'),
    url(r'^editorial/production/proofs$',
        TemplateView.as_view(template_name='guides/editorial/production/proofs.html'),
        name='proofs'),
    url(r'^editorial/production/online_publication$',
        TemplateView.as_view(template_name='guides/editorial/production/online_publication.html'),
        name='online_publication'),
]
