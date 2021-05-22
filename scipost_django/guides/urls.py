__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url
from django.contrib.auth.decorators import permission_required
from django.views.generic import TemplateView

app_name = 'guides'

urlpatterns = [
    url(r'^$',
        permission_required('scipost.can_view_docs_scipost')(
            TemplateView.as_view(template_name='guides/guides_index.html')),
        name='guides_index'),
    url(r'^editorial/submissions/submission_processing$',
        permission_required('scipost.can_view_docs_scipost')(
        TemplateView.as_view(
            template_name='guides/editorial/submissions/submission_prescreening.html')),
        name='submission_prescreening'),
    url(r'^editorial/production/initial_production$',
        permission_required('scipost.can_view_docs_scipost')(
        TemplateView.as_view(template_name='guides/editorial/production/initial_production.html')),
        name='initial_production'),
    url(r'^editorial/production/proofs$',
        permission_required('scipost.can_view_docs_scipost')(
        TemplateView.as_view(template_name='guides/editorial/production/proofs.html')),
        name='proofs'),
    url(r'^editorial/production/online_publication$',
        permission_required('scipost.can_view_docs_scipost')(
        TemplateView.as_view(template_name='guides/editorial/production/online_publication.html')),
        name='online_publication'),
]
