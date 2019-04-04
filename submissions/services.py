__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django import forms
from django.conf import settings

from .helpers import retrieve_pdf_from_arxiv
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
