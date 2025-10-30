__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import os
import subprocess


def remove_file_metadata(
    file_path: str,
    keywords: list[str],
    all_but_given: bool = False,
    blocking: bool = False,
):
    """
    Remove metadata from a file using exiftool.
    - `file_path`: path to the file to be cleaned
    - `keywords`: list of keywords to be removed if `all_but_given` is False, or to be kept if `all_but_given` is True
    - `blocking`: whether to block the main thread until the subprocess has finished
    """

    # launch subprocess to remove metadata from file, e.g.
    # exiftool -overwrite_original -all= -tagsFromFile @ -“Title” -“Page Count” filename.pdf
    p = subprocess.Popen(
        [
            "exiftool",
            "-overwrite_original",
            *(["-all=", "-tagsFromFile", "@"] if all_but_given else []),
            *[f"-{keyword}" for keyword in keywords],
            file_path,
        ],
    )

    if blocking:
        p.wait()


def linearize_pdf(file_path: str, blocking: bool = False):
    """
    Linearize a PDF file using qpdf.
    - `file_path`: path to the file to be linearized
    - `blocking`: whether to block the main thread until the subprocess has finished
    """
    p = subprocess.Popen(["qpdf", "--linearize", file_path, "--replace-input"])

    if blocking:
        p.wait()


def clean_pdf(file_path: str):
    """
    Clean the PDF file, removing metadata and linearizing it.
    """

    # TODO Do not fail silently, but raise an exception
    if not file_path.endswith(".pdf"):
        # raise ValueError("File must be a PDF")
        return

    if not os.path.isfile(file_path):
        # raise FileNotFoundError(f"File {file_path} does not exist")
        return

    # backup original file
    subprocess.run(["cp", file_path, file_path + ".bak"])

    try:
        remove_file_metadata(
            file_path,
            [
                "title",
                "producer",
                "creator",
                "createdate",
                "modifydate",
            ],
            all_but_given=True,
            blocking=True,
        )

        linearize_pdf(file_path)

    except subprocess.CalledProcessError as e:
        print(f"Error while processing file {file_path}: {e}")
        # restore original file
        subprocess.run(["rm", file_path])
        subprocess.run(["mv", file_path + ".bak", file_path])

    # Delete intermediate files
    subprocess.run(["rm", file_path + ".~qpdf-orig"])

    # TODO Remove the backup file after we are sure it is not needed anymore
