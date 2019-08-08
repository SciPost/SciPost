__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import os

from django.conf import settings
from django.core.management.base import BaseCommand

from journals.models import Issue


class Command(BaseCommand):
    """
    Verify path of issue publications and deposits; if wrong, repair.

    This command was written to repair the incorrect folder structure of SciPostPhys
    volume 5 issue 6, volume 6 issues 1, 2 and 3 (2019-08-08).
    """

    help = 'Repairs the paths of an issue, including its publications and deposits'

    def add_arguments(self, parser):
        parser.add_argument(
            '--issue_doi_label', choices=[issue.doi_label for issue in Issue.objects.all()],
            action='store', dest='issue_doi_label',
            help='doi label of the issue to repair'
        )

    def handle(self, *args, **kwargs):
        issue = Issue.objects.get(doi_label=kwargs['issue_doi_label'])
        print('media root: %s' % settings.MEDIA_ROOT)
        print('issue path: %s' % issue.path)
        if ('/%s/%s' % (issue.in_volume.number, issue.number)) not in issue.path:
            print('WARNING: /%s/%s not in issue path %s' % (
                issue.in_volume.number, issue.number, issue.path))
            # repair the issue path
            old_issue_path = issue.path
            issue_path = 'SCIPOST_JOURNALS/{name}/{volnr}/{issuenr}'.format(
                name=issue.in_volume.in_journal.name,
                volnr=issue.in_volume.number,
                issuenr=issue.number)
            issue.path = issue_path
            issue.save()
            print('New issue path: %s' % issue.path)
            for pub in issue.publications.all():
                print('\t%s' % pub.doi_label)
                old_dir = old_issue_path + '/{paper_nr}'.format(paper_nr=pub.get_paper_nr())
                new_dir = issue_path + '/{paper_nr}'.format(paper_nr=pub.get_paper_nr())
                os.makedirs(settings.MEDIA_ROOT + new_dir, exist_ok=True)
                new_pub_path = new_dir + '/{doi}.pdf'.format(doi=pub.doi_label.replace('.', '_'))
                os.rename(pub.pdf_file.path, settings.MEDIA_ROOT + new_pub_path)
                pub.pdf_file.name = new_pub_path
                pub.save()
                print('\t%s' % pub.pdf_file.path)
                # Move the timestamped files
                for deposit in pub.deposit_set.all():
                    new_dep_path = new_dir + '/{doi}_Crossref_{timestamp}.xml'.format(
                        doi=pub.doi_label.replace('.', '_'),
                        timestamp=deposit.timestamp)
                    os.rename(deposit.metadata_xml_file.path, settings.MEDIA_ROOT + new_dep_path)
                    deposit.metadata_xml_file.name = new_dep_path
                    deposit.save()
                    print('\t\t%s' % deposit.metadata_xml_file.path)
                # Now move the latest (non-timestamped) one
                old_dep_path = old_dir + '/{doi}_Crossref.xml'.format(
                    paper_nr=pub.get_paper_nr(),
                    doi=pub.doi_label.replace('.', '_'))
                new_dep_path = new_dir + '/{doi}_Crossref.xml'.format(
                    paper_nr=pub.get_paper_nr(),
                    doi=pub.doi_label.replace('.', '_'))
                os.rename(settings.MEDIA_ROOT + old_dep_path, settings.MEDIA_ROOT + new_dep_path)

                for deposit in pub.doajdeposit_set.all():
                    new_dep_path = new_dir + '/{doi}_DOAJ_{timestamp}.json'.format(
                        doi=pub.doi_label.replace('.', '_'),
                        timestamp=deposit.timestamp)
                    os.rename(deposit.metadata_DOAJ_file.path, settings.MEDIA_ROOT + new_dep_path)
                    deposit.metadata_DOAJ_file.name = new_dep_path
                    deposit.save()
                    print('\t\t%s' % deposit.metadata_DOAJ_file.path)
                old_dep_path = old_dir + '/{doi}_DOAJ.json'.format(
                    paper_nr=pub.get_paper_nr(),
                    doi=pub.doi_label.replace('.', '_'))
                new_dep_path = new_dir + '/{doi}_DOAJ.json'.format(
                    paper_nr=pub.get_paper_nr(),
                    doi=pub.doi_label.replace('.', '_'))
                os.rename(settings.MEDIA_ROOT + old_dep_path, settings.MEDIA_ROOT + new_dep_path)

                # Remove unneeded directories
                os.rmdir(settings.MEDIA_ROOT + old_dir + '/{doi}_Crossref'.format(
                    paper_nr=pub.get_paper_nr(),
                    doi=pub.doi_label.replace('.', '_')))
                os.rmdir(settings.MEDIA_ROOT + old_dir + '/{doi}_DOAJ'.format(
                    paper_nr=pub.get_paper_nr(),
                    doi=pub.doi_label.replace('.', '_')))
                os.rmdir(settings.MEDIA_ROOT + old_dir)
