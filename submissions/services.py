__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.conf import settings

from .helpers import retrieve_pdf_from_arxiv
from .models import iThenticateReport
from .plagiarism import iThenticate


class iThenticateCaller:
    def __init__(self, submission, document_id=None):
        self.document_id = document_id
        self.submission = submission

    def _get_client(self):
        client = iThenticate.API.Client(
            settings.ITHENTICATE_USERNAME, settings.ITHENTICATE_PASSWORD)
        if client.login():
            return client
        self.add_error(None, "Failed to login to iThenticate.")  # To do: wrong
        return None

    def update_status(self):
        if not self.document_id:
            return False

        # ...

    def upload_document(self, document=None):
        if self.document_id:
            # Wrong action?
            return None

        if not document:
            # Expect: ArxivPDFNotFound exception
            document = retrieve_pdf_from_arxiv(self.submission.preprint.identifier_w_vn_nr)

        client = self._get_client()
        if not client:
            return None

         try:
            plagiarism = iThenticate()
            data = plagiarism.upload_submission(document, self.submission)

            # Give feedback to the user
            if not data:
                self.add_error(None, "Updating failed. iThenticate didn't return valid data [3]")  # To do: . wrong
                for msg in plagiarism.get_messages():
                    self.add_error(None, msg)  # To do: wrong.
                return None
            except AttributeError:
                # To do: all wrong...
                if not self.fields.get('file'):
                    # The document is invalid.
                    self.add_error(None, ('A valid pdf could not be found at arXiv.'
                                          ' Please upload the pdf manually.'))
                else:
                    self.add_error(None, ('The uploaded file is not valid.'
                                          ' Please upload a valid pdf.'))
                self.fields['file'] = forms.FileField()

        return data

# class iThenticateReportForm(forms.ModelForm):
#     class Meta:
#         model = iThenticateReport
#         fields = []
#
#     def __init__(self, submission, *args, **kwargs):
#         self.submission = submission
#         super().__init__(*args, **kwargs)
#
#         if kwargs.get('files', {}).get('file'):
#             # Add file field if file data is coming in!
#             self.fields['file'] = forms.FileField()
#
#     def clean(self):
#         cleaned_data = super().clean()
#         doc_id = self.instance.doc_id
#         if not doc_id and not self.fields.get('file'):
#             try:
#                 cleaned_data['document'] = helpers.retrieve_pdf_from_arxiv(
#                     self.submission.preprint.identifier_w_vn_nr)
#             except exceptions.ArxivPDFNotFound:
#                 self.add_error(
#                     None, 'The pdf could not be found at arXiv. Please upload the pdf manually.')
#                 self.fields['file'] = forms.FileField()
#         elif not doc_id and cleaned_data.get('file'):
#             cleaned_data['document'] = cleaned_data['file'].read()
#         elif doc_id:
#             self.document_id = doc_id
#
#         # Login client to append login-check to form
#         self.client = self.get_client()
#
#         if not self.client:
#             return None
#
#         # Document (id) is found
#         if cleaned_data.get('document'):
#             self.document = cleaned_data['document']
#             try:
#                 self.response = self.call_ithenticate()
#             except AttributeError:
#                 if not self.fields.get('file'):
#                     # The document is invalid.
#                     self.add_error(None, ('A valid pdf could not be found at arXiv.'
#                                           ' Please upload the pdf manually.'))
#                 else:
#                     self.add_error(None, ('The uploaded file is not valid.'
#                                           ' Please upload a valid pdf.'))
#                 self.fields['file'] = forms.FileField()
#         elif hasattr(self, 'document_id'):
#             self.response = self.call_ithenticate()
#
#         if hasattr(self, 'response') and self.response:
#             return cleaned_data
#
#         # Don't return anything as someone submitted invalid data for the form at this point!
#         return None
#
#     def save(self, *args, **kwargs):
#         data = self.response
#
#         report, created = iThenticateReport.objects.get_or_create(doc_id=data['id'])
#
#         if not created:
#             try:
#                 iThenticateReport.objects.filter(doc_id=data['id']).update(
#                     uploaded_time=data['uploaded_time'],
#                     processed_time=data['processed_time'],
#                     percent_match=data['percent_match'],
#                     part_id=data.get('parts', [{}])[0].get('id')
#                 )
#             except KeyError:
#                 pass
#         else:
#             report.save()
#             Submission.objects.filter(id=self.submission.id).update(plagiarism_report=report)
#         return report
#
#     def call_ithenticate(self):
#         if hasattr(self, 'document_id'):
#             # Update iThenticate status
#             return self.update_status()
#         elif hasattr(self, 'document'):
#             # Upload iThenticate document first time
#             return self.upload_document()
#
#     def get_client(self):
#         client = iThenticate.API.Client(settings.ITHENTICATE_USERNAME,
#                                         settings.ITHENTICATE_PASSWORD)
#         if client.login():
#             return client
#         self.add_error(None, "Failed to login to iThenticate.")
#         return None
#
#     def update_status(self):
#         client = self.client
#         response = client.documents.get(self.document_id)
#         if response['status'] == 200:
#             return response.get('data')[0].get('documents')[0]
#         self.add_error(None, "Updating failed. iThenticate didn't return valid data [1]")
#
#         for msg in client.messages:
#             self.add_error(None, msg)
#         return None
#
#     def upload_document(self):
#         from .plagiarism import iThenticate
#         plagiarism = iThenticate()
#         data = plagiarism.upload_submission(self.document, self.submission)
#
#         # Give feedback to the user
#         if not data:
#             self.add_error(None, "Updating failed. iThenticate didn't return valid data [3]")
#             for msg in plagiarism.get_messages():
#                 self.add_error(None, msg)
#             return None
#         return data
