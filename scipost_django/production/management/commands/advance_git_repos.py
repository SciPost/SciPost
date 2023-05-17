__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from typing import Any, Dict, List
from django.core.management.base import BaseCommand, CommandParser
from django.conf import settings

from common.utils import get_current_domain

from gitlab import Gitlab
from gitlab.v4.objects import Group, Project
from gitlab.exceptions import GitlabGetError


from production.models import ProofsRepository
from production.constants import (
    PROOFS_REPO_UNINITIALIZED,
    PROOFS_REPO_CREATED,
    PROOFS_REPO_TEMPLATE_ONLY,
    PROOFS_REPO_TEMPLATE_FORMATTED,
    PROOFS_REPO_PRODUCTION_READY,
)


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
            type=int,
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

        GL = Gitlab(url=settings.GITLAB_URL, private_token=settings.GITLAB_KEY)

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
                        f"The parent group of {path_up_to_segment_i} does not exist. \
                        This should not happen normally (and would not be fixable \
                        because GitLab does not allow root groups to be created)."
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

        self.stdout.write(
            self.style.SUCCESS(f"Created git repository at {repo.git_path}")
        )

    def _get_project_cloning_actions(self, project: Project) -> List[Dict[str, Any]]:
        """
        Return a list of gitlab actions required to fully clone a project.
        """
        files = list(map(lambda x: x["path"], project.repository_tree(get_all=True)))

        actions = []
        for filename in files:
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

        journal_template_project = self.GL.projects.get(repo.template_path)
        base_template_project = self.GL.projects.get(
            "{ROOT}/Templates/Base".format(ROOT=settings.GITLAB_ROOT)
        )

        base_actions = self._get_project_cloning_actions(base_template_project)
        journal_actions = self._get_project_cloning_actions(journal_template_project)

        # Commit the actions
        project.commits.create(
            {
                "branch": "main",
                "commit_message": "copy pure templates",
                "actions": base_actions + journal_actions,
            }
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
        repos_to_be_created = repos.filter(status=PROOFS_REPO_UNINITIALIZED)
        for repo in repos_to_be_created:
            self._create_git_repo(repo)
            repo.status = PROOFS_REPO_CREATED
            repo.save()

        # Copy the pure templates
        repos_to_be_templated = repos.filter(status=PROOFS_REPO_CREATED)
        for repo in repos_to_be_templated:
            self._copy_pure_templates(repo)
            repo.status = PROOFS_REPO_TEMPLATE_ONLY
            repo.save()
