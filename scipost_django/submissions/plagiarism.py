__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf import settings

from .exceptions import InvalidDocumentError

import iThenticate as iThenticateAPI


class iThenticate:
    def __init__(self):
        self.client = self.get_client()

    def get_client(self):
        client = iThenticateAPI.API.Client(
            settings.ITHENTICATE_USERNAME, settings.ITHENTICATE_PASSWORD)
        if client.login():
            return client
        self.add_error(None, "Failed to login to iThenticate.")
        return None

    def determine_folder_group(self, group_re):
        """Return the folder group id to which the system should upload a new document to.

        Generates a new folder group if needed.
        """
        groups = self.client.groups.all()
        if groups['status'] != 200:
            raise InvalidDocumentError("Uploading failed. iThenticate didn't return"
                                       " valid data [4]: %s" % self.client.messages[0])

        for group in groups['data'][0].get('groups'):
            # Found the group
            if group.get('name', '') == group_re:
                return group['id']

        # Create a new group
        response = self.client.groups.add(group_re)

        if response['status'] != 200:
            raise InvalidDocumentError("Failed creating a new Folder Group [5].")

        return response['data'][0]['id']

    def determine_folder_id(self, submission):
        """Return the folder id to which the system should upload a new document to.

        Generates a new folder and id if needed.
        """
        group_re = '{journal}_submissions'.format(journal=submission.submitted_to.doi_label)
        folder_re = '{year}_{month}'.format(
            year=submission.submission_date.year,
            month=submission.submission_date.month
        )
        all_folders = self.client.folders.all()
        if all_folders['status'] != 200:
            raise InvalidDocumentError("Uploading failed. iThenticate didn't return"
                                       " valid data [2]: %s" % self.client.messages[0])

        # Iterate folders as the api doesn't allow for a search
        for folder in all_folders['data'][0].get('folders'):
            # Found right folder!
            if folder.get('name', '') == folder_re and folder.get('group', {}).get('name'):
                return folder['id']

        group_id = self.determine_folder_group(group_re)

        # Create new folder
        data = self.client.folders.add(group_id, folder_re)
        if data['status'] != 200:
            raise InvalidDocumentError("Failed to create a new folder [3].")

        return data['data'][0]['id']

    def upload_submission(self, document, submission):
        """Upload a document related to a submission.

        :document: The document to upload
        :submission: submission which should be uploaded
        """
        folder_id = self.determine_folder_id(submission)

        # Finally, upload the file
        author = submission.authors.first()
        response = self.client.documents.add(
            document,
            folder_id,
            author.user.first_name,
            author.user.last_name,
            submission.title,
        )

        if response['status'] == 200:
            submission.add_general_event('The document has been submitted for a plagiarism check.')
            return response.get('data', [{'uploaded': [{}]}])[0].get('uploaded')[0]
        return None

    def get_url(self, document_id):
        """Return report url for given document."""
        response = self.client.reports.get(document_id)

        if response['status'] == 200:
            return response['data'][0].get('view_only_url')
        return None

    def get_messages(self):
        return self.client.messages
