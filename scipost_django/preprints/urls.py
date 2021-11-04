__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path

from . import views


app_name = 'preprints'

urlpatterns = [
    path(
        '<identifier_wo_vn_nr:identifier_wo_vn_nr>/',
        views.preprint_pdf_wo_vn_nr,
        name='preprint_wo_vn_nr'
    ),
    path(
        '<identifier:identifier_w_vn_nr>/',
        views.preprint_pdf,
        name='pdf'
    ),
]
