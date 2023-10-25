__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from datetime import datetime
from functools import reduce
from itertools import chain, cycle
from typing import Any, Callable, Dict, List, Tuple
from time import sleep

from django.core.management.base import BaseCommand, CommandParser
from django.conf import settings

from common.utils import get_current_domain

from gitlab import Gitlab
from gitlab.v4.objects import Group, Project
from gitlab.exceptions import GitlabGetError
from gitlab.const import AccessLevel

import arxiv
import requests
import tarfile
from base64 import b64encode


from production.models import ProofsRepository, ProductionUser, ProductionEvent


class Command(BaseCommand):
    """
    This command handles the creation and updating of git repositories.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # Check that the global GITLAB_ROOT constant is set
        if not hasattr(settings, "GITLAB_ROOT") or settings.GITLAB_ROOT == "":
            raise LookupError(
                "Constant `GITLAB_ROOT` is either not present in settings file or empty, please add it."
            )

        self.GL: Gitlab = self._instanciate_gitlab()

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--id",
            type=str,
            required=False,
            help="The submission preprint identifier to handle a specific submission, leave blank to handle all",
        )

    def _instanciate_gitlab(self) -> Gitlab:
        """
        Test the connection to the git server, returns a Gitlab object.
        """

        if not hasattr(settings, "GITLAB_KEY") or settings.GITLAB_KEY == "":
            raise LookupError(
                "Constant `GITLAB_KEY` is either not present in secret file or empty, please add it."
            )

        if not hasattr(settings, "GITLAB_URL") or settings.GITLAB_URL == "":
            raise LookupError(
                "Constant `GITLAB_URL` is either not present in secret file or empty, please add it."
            )

        GL = Gitlab(
            url="https://" + settings.GITLAB_URL,
            private_token=settings.GITLAB_KEY,
        )

        try:
            GL.auth()
        except Exception as e:
            raise AssertionError(
                "Could not authenticate with GitLab, please check your credentials."
            ) from e

        return GL

    def _get_or_create_nested_group(self, group_path: str) -> Group:
        """
        Create a new group on the git server based on a path of nested folders.
        """
        parent_group = None
        group_path_segments = group_path.split("/")

        # Traverse the path segments (up to the second-to-last one)
        # and create the groups if they do not exist
        for i, group_path_segment in enumerate(group_path_segments[:-1]):
            path_up_to_segment_i = "/".join(group_path_segments[: i + 1])

            # Check if group exists in the server
            try:
                group = self.GL.groups.get(path_up_to_segment_i)

            # If it does not exist, create it
            except GitlabGetError:
                # Guard against the root group not existing
                if parent_group is None:
                    raise AssertionError(
                        f"The parent group of {path_up_to_segment_i} does not exist. "
                        "This should not happen normally (and would not be fixable "
                        "because GitLab does not allow root groups to be created)."
                    )

                # Create the group
                group = self.GL.groups.create(
                    {
                        "name": group_path_segment,
                        "path": group_path_segment,
                        "parent_id": parent_group.id,
                        "visibility": "private",
                    }
                )

            # Set the parent group to the current group
            parent_group = group

        return group

    def _create_git_repo(self, repo: ProofsRepository):
        """
        Create a new git repository for the submission.
        """
        # Check if repo exists in the server
        try:
            project = self.GL.projects.get(repo.git_path)

        # Create the repo on the server
        except GitlabGetError:
            # Get the namespace id
            parent_group_id = self._get_or_create_nested_group(repo.git_path).id
            project = self.GL.projects.create(
                {
                    "name": repo.name,
                    "namespace_id": parent_group_id,
                    "visibility": "private",
                    "description": "Proofs for https://{domain}/submissions/{preprint_id}".format(
                        domain=get_current_domain(),
                        preprint_id=repo.stream.submission.preprint.identifier_w_vn_nr,
                    ),
                }
            )

            # Add event to the production stream
            if system_user := ProductionUser.objects.get(user__username="system"):
                ProductionEvent.objects.create(
                    stream=repo.stream,
                    event="status",
                    comments=f"Created git repository for proofs.",
                    noted_by=system_user,
                )

        self.stdout.write(
            self.style.SUCCESS(f"Created git repository at {repo.git_path}")
        )

    def _get_project_cloning_actions(self, project: Project) -> List[Dict[str, Any]]:
        """
        Return a list of gitlab actions required to fully clone a project.
        """
        try:
            filenames = list(
                map(lambda x: x["path"], project.repository_tree(get_all=True))
            )
        except:
            self.stdout.write(
                self.style.WARNING(
                    f"Could not get the files of {project.path_with_namespace}, it may be empty"
                )
            )
            return []

        actions = []
        for filename in filenames:
            try:
                file = project.files.get(file_path=filename, ref="main")
            except:
                self.stdout.write(
                    self.style.WARNING(f"File {filename} not found in {project.name}")
                )
                continue

            actions.append(
                {
                    "action": "create",
                    "file_path": filename,
                    "content": file.content,
                    "encoding": "base64",
                }
            )

        return actions

    def _copy_pure_templates(self, repo: ProofsRepository):
        """
        Copy the pure templates to the repo.
        """
        project = self.GL.projects.get(repo.git_path)

        # Get the cloning actions for each template project
        actions = [
            self._get_project_cloning_actions(self.GL.projects.get(template_path))
            for template_path in repo.template_paths
        ]
        actions = list(chain(*actions))  # Flatten the list of lists

        # Keep the last action if there are multiple actions for the same file
        # (i.e. the same file_path key in the dictionary)
        non_duplicate_actions = []
        file_paths_to_clone = []

        for action in reversed(actions):
            file_path = action.get("file_path", None)
            if (file_path is not None) and (file_path not in file_paths_to_clone):
                file_paths_to_clone.append(file_path)
                non_duplicate_actions.append(action)

        # Add some delays to avoid:
        # - Commiting the files before the branch has finished being created
        # - Changing the protected branch before the files have been commited
        sleep(3)
        # Commit the actions
        project.commits.create(
            {
                "branch": "main",
                "commit_message": "copy pure templates",
                "actions": non_duplicate_actions,
            }
        )
        sleep(3)

        # Allow Developers to push to the protected "main" branch
        # Protected branches lay on top of the branches. Deleting and recreating them is
        # the only way to change their settings and does not affect the branches themselves
        project.protectedbranches.delete("main")
        project.protectedbranches.create(
            {
                "name": "main",
                "merge_access_level": AccessLevel.MAINTAINER,
                "push_access_level": AccessLevel.DEVELOPER,
                "allow_force_push": False,
            }
        )

        self.stdout.write(
            self.style.SUCCESS(f"Copied pure templates to {repo.git_path}")
        )

    def _format_skeleton(self, repo: ProofsRepository):
        """
        Format the Skeleton.tex file of the repo to include basic information about the submission.
        """

        SHAPES = ["star", "dagger", "ddagger", "circ", "S", "P", "parallel"]
        SLASH = "\\"
        NEWLINE = f"{SLASH}{SLASH}"

        def abbreviate_author(author: str) -> str:
            """
            Abbreviate an author's name by taking the first letter\
            of their first and middle names, and their full last name.
            """

            # TODO: This is somewhat naive, but it should work for now.
            first_name, *middle_names, last_name = author.split(" ")
            # Ideally, I would like to search for matching authors in the database
            # and abbreviate their names accordingly to the journal's style.
            # Right now, I abbreviate only the very first name and leave the rest as is.

            # Map each part of the (optionally) hyphenated first name to its abbreviation
            # (e.g. "John-Edward" -> "J.-E.")
            first_name_hyphen_parts = first_name.split("-")
            first_name_hyphen_parts_abbrev = list(
                map(lambda x: x[0].upper() + ".", first_name_hyphen_parts)
            )

            # Add different name parts to the abbreviation, glue them together with space
            # (e.g. "John-Edward Brown Smith" -> "J.-E. Brown Smith")
            abbreviation_parts = [
                "-".join(first_name_hyphen_parts_abbrev),  # Abbreviated first name
                *middle_names,
                last_name,
            ]

            return " ".join(abbreviation_parts)

        # Define the formatting functions
        def format_authors(authors: List[str]) -> str:
            # Append a superscript to each author
            authors = [
                author + "\\textsuperscript{" + str(i) + "}"
                for i, author in enumerate(authors, start=1)
            ]

            *other_authors, last_author = authors

            if len(other_authors) == 0:
                return last_author
            else:
                return ",\n".join(other_authors) + "\nand " + last_author

        def format_title(title: str) -> str:
            return title + NEWLINE

        def format_copyright(authors: List[str]) -> str:
            """
            Format the copyright statement depending on the number\
            of authors in the submission:
            - 1 author: "© Author"
            - 2 authors: "© Author1 and Author2"
            - 3+ authors: "© Author1 et al"
            """
            if len(authors) == 1:
                return f"Copyright {authors[0]}"
            elif len(authors) == 2:
                return f"Copyright {authors[0]} and {authors[1]}"
            else:
                return f"Copyright {authors[0]} {{{SLASH}it et al}}"

        def format_emails(authors: List[str]) -> str:
            """
            Format the emails of the authors in the submission, grouped by 3 per line.\
            The emails are padded with \\quad spacing and are prepended with a shape.
            """
            # Create a list array of emails, grouped by 3
            mail_lines = [[]]
            mail_line_i = 0
            for i, (_, shape) in enumerate(zip(authors, cycle(SHAPES))):
                mail_lines[mail_line_i].append(
                    f"${SLASH}{shape}$ {SLASH}href{{mailto:email{i+1}}}{{{SLASH}small email{i+1}}}"
                )

                # Create a new mail group every 3 emails
                if (i + 1) % 3 == 0:
                    mail_line_i += 1
                    mail_lines.append([])

            # Flatten the inner lists and join them with "\,,\quad"
            flattened_mail_lines = [
                f"{SLASH},,{SLASH}quad\n".join(line) for line in mail_lines
            ]

            # Join the lines with "\,,\\"
            flattened_mails = f"{SLASH},,{NEWLINE}\n".join(flattened_mail_lines)

            return flattened_mails

        def format_affiliations(authors: List[str]) -> str:
            """
            Format the affiliations of the authors in the submission,
            by including the author's name and the affiliation number.
            There is one affiliation per author by default.
            """
            affiliations = []
            for i, author in enumerate(authors):
                affiliations += [f"{{{SLASH}bf {i+1}}} Affiliation {author}"]

            return f"\n{NEWLINE}\n".join(affiliations)

        def format_date_human_readable(date: datetime) -> str:
            """
            Format a date in a human-readable format (DD-MM-YYY).
            """
            return date.strftime("%d-%m-%Y")

        project = self.GL.projects.get(repo.git_path)
        project_filenames = list(
            map(lambda x: x["path"], project.repository_tree(get_all=True))
        )

        skeleton_filename = next(
            filter(lambda x: x.endswith("Skeleton.tex"), project_filenames)
        )
        skeleton_file = project.files.get(file_path=skeleton_filename, ref="main")
        skeleton_content = skeleton_file.decode().decode("utf-8")

        # Collect the information about the paper
        paper_title = repo.stream.submission.title
        paper_abbreviated_authors = list(
            map(abbreviate_author, repo.stream.submission.authors_as_list)
        )
        paper_received_date = repo.stream.submission.original_submission_date
        paper_acceptance_date = repo.stream.submission.acceptance_date

        # Create the replacement dictionary from placeholders and information
        # key = placeholder, value = (formatting_function, *args)
        replacements_dict = {
            "<|TITLE|>": (format_title, paper_title),
            "<|AUTHORS|>": (format_authors, repo.stream.submission.authors_as_list),
            "<|EMAILS|>": (format_emails, paper_abbreviated_authors),
            "<|COPYRIGHT|>": (format_copyright, paper_abbreviated_authors),
            "<|AFFILIATIONS|>": (format_affiliations, paper_abbreviated_authors),
            "<|RECEIVED|>": (format_date_human_readable, paper_received_date),
            "<|ACCEPTED|>": (format_date_human_readable, paper_acceptance_date),
        }

        # Replace the logo if the submission has been accepted in Selections
        if "Selections" in repo.stream.submission.editorial_decision.for_journal.name:
            default_logo_img = r"[width=20mm]{logo_scipost_with_bgd.pdf}"
            selections_logo_img = r"[width=34.55mm]{logo_select.pdf}"
            replacements_dict[default_logo_img] = (lambda _: selections_logo_img, None)

        # Add collection specific information if the submission is part of a collection
        if repo.stream.submission.collections.exists():
            collection = repo.stream.submission.collections.first()
            series = collection.series

            collection_replacements_dict = {
                "<|COLLECTION_NAME|>": (lambda _: collection.name, None),
                "<|COLLECTION_URL|>": (lambda _: collection.get_absolute_url(), None),
                "<|EVENT_DETAILS|>": (lambda _: collection.event_details, None),
                "<|SERIES_NAME|>": (lambda _: series.name, None),
                "<|SERIES_URL|>": (lambda _: series.get_absolute_url(), None),
            }

            replacements_dict.update(collection_replacements_dict)

        # Define a helper function to try to format and replace a placeholder
        # which catches any errors and prints them to the console non-intrusively
        def try_format_replace(
            text: str,
            key: str,
            value: Tuple[Callable[[Any], str], Any],
        ):
            try:
                formatting_function, *args = value
                formatted_value = formatting_function(*args)
                return text.replace(key, formatted_value)
            except:
                self.stdout.write(
                    self.style.ERROR(
                        f"Could not format and replace {key} with {value} in {repo.git_path}"
                    )
                )
                return text

        # Replace the placeholders with the submission information
        # by iteratively applying the formatting functions to the skeleton
        skeleton_content = reduce(
            lambda text, replace_pair: try_format_replace(text, *replace_pair),
            replacements_dict.items(),
            skeleton_content,
        )

        # Commit the changes to the skeleton file and change its name
        project.commits.create(
            {
                "branch": "main",
                "commit_message": f"format skeleton file",
                "actions": [
                    {
                        "action": "move",
                        "content": skeleton_content,
                        "previous_path": skeleton_filename,
                        # Change the "Skeleton" part from the filename to the repo name
                        # and remove the extraneous "scipost_" label from the identifier slug
                        "file_path": skeleton_filename.replace(
                            "Skeleton",
                            repo.name.replace("scipost_", ""),
                        ),
                    },
                ],
            }
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully formatted the skeleton of {repo.git_path}"
            )
        )

    def _copy_arxiv_source_files(self, repo: ProofsRepository):
        paper = next(
            arxiv.Search(
                id_list=[repo.stream.submission.preprint.identifier_w_vn_nr]
            ).results()
        )
        source_stream = requests.get(paper.pdf_url.replace("pdf", "src"), stream=True)

        # Create file creation actions for each file in the source tar
        actions = []
        with tarfile.open(fileobj=source_stream.raw) as tar:
            for member in tar:
                if not member.isfile():
                    continue

                f = tar.extractfile(member)
                try:
                    bin_content = f.read()
                    actions.append(
                        {
                            "action": "create",
                            "file_path": member.name,
                            "encoding": "base64",
                            # Encode the binary content in base64, required by the API
                            "content": b64encode(bin_content).decode("utf-8"),
                        }
                    )

                except:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Could not read {member.name} from the arXiv source files, skipping..."
                        )
                    )

        # Filter out the files that already exist in the repo to avoid conflicts
        project = self.GL.projects.get(repo.git_path)
        project_existing_filenames = list(
            map(lambda x: x["path"], project.repository_tree(get_all=True))
        )

        non_existing_file_actions = [
            action
            for action in actions
            if action["file_path"] not in project_existing_filenames
        ]

        # Commit the creation of the files
        project.commits.create(
            {
                "branch": "main",
                "commit_message": f"copy arXiv source files",
                "actions": non_existing_file_actions,
            }
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully copied the author source files to {repo.git_path}"
            )
        )

    def handle(self, *args, **options):
        # Limit the actions to a specific submission if requested
        if preprint_id := options.get("id"):
            repos = ProofsRepository.objects.filter(
                stream__submission__preprint__identifier_w_vn_nr=preprint_id
            )
        else:
            repos = ProofsRepository.objects.all()

        # Create the repos
        repos_to_be_created = repos.filter(
            status=ProofsRepository.PROOFS_REPO_UNINITIALIZED
        )
        for repo in repos_to_be_created:
            # Skip repos whose streams that are in stasis
            if repo.stream.in_stasis:
                continue
            try:
                self._create_git_repo(repo)
                repo.status = ProofsRepository.PROOFS_REPO_CREATED
                repo.save()
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Could not create the git repo for {repo.git_path}, error: {e}"
                    )
                )

        # Copy the pure templates
        repos_to_be_templated = repos.filter(
            status=ProofsRepository.PROOFS_REPO_CREATED
        )
        for repo in repos_to_be_templated:
            try:
                self._copy_pure_templates(repo)
                repo.status = ProofsRepository.PROOFS_REPO_TEMPLATE_ONLY
                repo.save()
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Could not copy the pure templates to {repo.git_path}, error: {e}"
                    )
                )

        # Format the skeleton files
        repos_to_be_formatted = repos.filter(
            status=ProofsRepository.PROOFS_REPO_TEMPLATE_ONLY
        )
        for repo in repos_to_be_formatted:
            if repo.journal_abbrev == "MigPol":
                # We cannot format the skeleton of MigPol because it is not a LaTeX file
                repo.status = ProofsRepository.PROOFS_REPO_TEMPLATE_FORMATTED
                repo.save()
                continue

            try:
                self._format_skeleton(repo)
                repo.status = ProofsRepository.PROOFS_REPO_TEMPLATE_FORMATTED
                repo.save()
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Could not format the skeleton of {repo.git_path}, error: {e}"
                    )
                )

        # Copy the arXiv source files
        repos_to_be_copied = repos.filter(
            status=ProofsRepository.PROOFS_REPO_TEMPLATE_FORMATTED
        )
        for repo in repos_to_be_copied:
            try:
                if "arxiv.org" in repo.stream.submission.preprint.url:
                    self._copy_arxiv_source_files(repo)
                    repo.status = ProofsRepository.PROOFS_REPO_PRODUCTION_READY
                    repo.save()
                else:
                    # We cannot automatically copy the source files of non-arXiv submissions
                    repo.status = ProofsRepository.PROOFS_REPO_PRODUCTION_READY
                    repo.save()

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Could not copy the arXiv source files to {repo.git_path}, error: {e}"
                    )
                )
