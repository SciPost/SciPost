__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone

from tqdm import tqdm

from SciPost_v1.settings.base import get_secret
from journals.constants import INDIVIDUAL_PUBLICATIONS, ISSUES_AND_VOLUMES, ISSUES_ONLY
from journals.models import Journal, Issue

from pathlib import Path
import tarfile
import ftplib

MEDIA_ROOT = Path(settings.MEDIA_ROOT)
PUBFILES_DIR = MEDIA_ROOT / Path(settings.JOURNALS_DIR)
ARCHIVE_DIR = PUBFILES_DIR / Path("ARCHIVE")


class Command(BaseCommand):
    help = "Copy publications and metadata to an appropriate .tar archive and push via FTP to CLOCKSS."

    def add_arguments(self, parser):
        parser.add_argument(
            "--doi",
            action="store",
            default=None,
            type=str,
            help="DOI of the publication (container) to add to the archive. If not specified, all publications will be added.",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            default=False,
            help="Overwrite existing files when archiving.",
        )

    def handle(self, *args, **kwargs):
        if kwargs.get("doi"):
            raise NotImplementedError(
                "Archiving a single publication container is not yet implemented."
            )

        now = timezone.now()
        file_map: dict[Path, list[Path]] = {}
        for journal in tqdm(
            Journal.objects.all(), desc="Determining journal files to archive"
        ):
            if journal.structure == INDIVIDUAL_PUBLICATIONS:
                file_map.update(self.get_container_files_to_archive(journal))
            elif journal.structure == ISSUES_ONLY:
                for issue in journal.issues.filter(until_date__lt=now):
                    file_map.update(self.get_container_files_to_archive(issue))
            elif journal.structure == ISSUES_AND_VOLUMES:
                for volume in journal.volumes.filter(until_date__lt=now):
                    for issue in volume.issues.filter(until_date__lt=now):
                        file_map.update(self.get_container_files_to_archive(issue))

        archive_paths_created: list[Path] = []
        for archive_path, file_paths in tqdm(
            file_map.items(), desc="Creating archives"
        ):
            archive_path_created = self.archive_files(archive_path, file_paths)
            if archive_path_created:
                archive_paths_created.append(archive_path_created)

        ftp_connection = self.create_ftp_connection()
        for archive_path in tqdm(
            archive_paths_created, desc="Uploading archives to CLOCKSS"
        ):
            self.upload_archive_to_CLOCKSS(
                ftp_connection,
                archive_path,
                overwrite=kwargs.get("overwrite", False),
            )

        ftp_connection.quit()

    def create_ftp_connection(self):
        ftp = ftplib.FTP(get_secret("CLOCKSS_FTP_HOST"))
        ftp.login(get_secret("CLOCKSS_FTP_USER"), get_secret("CLOCKSS_FTP_PASSWORD"))
        return ftp

    def get_container_files_to_archive(self, container: Journal | Issue):
        """
        Returns a dictionary mapping archive paths to lists of publication file paths for the given container (Journal or Issue).
        """

        archive_file_map: dict[Path, list[Path]] = {}

        container_parts = []
        if isinstance(container, Journal):
            container_parts = [container.doi_label]
        elif isinstance(container, Issue):
            if container.in_volume:
                container_parts = (
                    container.in_volume.in_journal.doi_label,
                    str(container.in_volume.number),
                    str(container.number),
                )
            elif container.in_journal:
                container_parts = (
                    container.in_journal.doi_label,
                    str(container.number),
                )
        else:
            raise ValueError("Container must be a Journal or an Issue")

        container_path = Path("/".join(container_parts))
        publication_paths = sorted((PUBFILES_DIR / container_path).glob("[!.]*"))
        for publication_path in publication_paths:
            pub_relative_path = publication_path.relative_to(PUBFILES_DIR)

            # For journals, each publication is its separate archive
            # Squash the "container" to be each individual publication path
            if isinstance(container, Journal):
                container_path = pub_relative_path

            filename_tar = Path(".".join(container_path.parts + ("tar",)))

            # The container path should have at most two levels of nesting (journal + ...)
            trunc_container_path = Path(*container_path.parts[:2])

            archive_path = ARCHIVE_DIR / trunc_container_path / filename_tar

            filename_base = Path("_".join(pub_relative_path.parts))
            filename_pdf = filename_base.with_suffix(".pdf")
            filename_metadata = filename_base.with_name(
                filename_base.name + "_Crossref"
            ).with_suffix(".xml")

            publication_file_paths = [
                PUBFILES_DIR / pub_relative_path / filename_pdf,
                PUBFILES_DIR / pub_relative_path / filename_metadata,
            ]

            if all(f.exists() for f in publication_file_paths):
                archive_file_map.setdefault(archive_path, []).extend(
                    publication_file_paths
                )

        return archive_file_map

    def archive_files(self, archive_path: Path, file_paths: list[Path]):
        """
        Creates a tar archive at the given path containing the specified files.
        The files will be stored in the archive with paths relative to PUBFILES_DIR.
        """
        if archive_path.exists():
            return  # Skip if the archive already exists

        archive_path.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive_path, "w") as archive_tar_file:
            for file_path in file_paths:
                file_path_inside_tar = file_path.relative_to(PUBFILES_DIR)
                archive_tar_file.add(file_path, arcname=file_path_inside_tar)

        return archive_path

    def upload_archive_to_CLOCKSS(
        self,
        connection: ftplib.FTP,
        archive_path: Path,
        overwrite: bool = False,
    ):
        """
        Uploads the given archive file to the CLOCKSS FTP server.
        """
        ftp_path = archive_path.relative_to(ARCHIVE_DIR)

        # Create parent path on the FTP server if it doesn't exist
        parent_path = ftp_path.parent
        try:
            connection.cwd(parent_path.as_posix())
        except ftplib.error_perm:
            # If the directory doesn't exist, create it
            connection.cwd("/")
            for part in ftp_path.parts[:-1]:
                try:
                    connection.mkd(part)
                except ftplib.error_perm:
                    pass  # Directory already exists
                connection.cwd(part)

        # Upload the archive file
        if connection.nlst(archive_path.name) and not overwrite:
            self.stdout.write(
                self.style.WARNING(
                    f"Archive {archive_path.name} already exists on CLOCKSS. "
                    "Use --overwrite to replace it."
                )
            )
            return

        with open(archive_path, "rb") as archive_file:
            connection.storbinary(f"STOR {archive_path.name}", archive_file)
