.. Howto for publication production

Production of SciPost Publications
==================================

This guide is meant for **Editorial Administrators** and **Production Officers**. It describes the post-acceptance workflow from paper acceptance to publication.

Version: 2016-12-20.


Formatting check
----------------

   If the Submission's references are not properly formatted,
   and/or if these do not include the required DOIs,
   the authors should be emailed and asked to do so,
   by providing either the ``.bbl`` file or the ``.bib`` source.


Source retrieval and folder preparation
---------------------------------------

   #. On the SciPost server, navigate to folder
      ``[Journal full name]/IN PRODUCTION``.
   #. Create a folder
      ``[journal abbrev. name]_[arxiv identifier]_[first author last name]``,
      e.g. ``SciPost_Phys_1604.98141v3_Smart``.
   #. Save the source from arXiv into this folder.
   #. NOTE: the file will be named ``####.#####v#``, which is not recognized
      as a ``.tar.gz`` file on a UNIX system. Rename the file
      ``####.####v#.tar.gz``. Unzip it to produce the folder ``####.#####v#``.
   #. Copy the paper’s sources one level down (so from ``####.#####v#`` to
      the current directory). BE CAREFUL: is the authors have included any of
      the SciPost style files (``SciPost.cls``, ``SciPost_bibstyle.bst``), DO NOT
      copy those down.
   #. Copy the files in
      ``[Journal full name]/v##_production/FILES_TO_COPY_IN_PAPER_DIR``
      to the current directory. There are 5 files:

         * ``by.eps``
	 * ``logo_scipost_with_bgd.pdf``
	 * ``SciPost_bibstyle.bst``
	 * ``SciPost.cls``
	 * ``SciPost_Phys_Skeleton.tex``

   #. Copy the skeleton ``.tex`` source to a new file using the name convention
      ``[Journal abbrev. name]_####_#####v#_[first author last name].tex``
      (careful: use underscore instead of . between numbers).


LaTeX file preparation
----------------------

   The next step is to transfer the submission's LaTeX contents into the final file.

   All steps involed appear in the skeleton ``.tex`` source in the form ``%%%%%%%%%% TODO: [TOKEN]`` opening marked, followed by a corresponding ``%%%%%%%%%% END TODO: [TOKEN]`` marker.


   During the file preparation, if there is anything worth noting about the
   production process, please include this in a::

     %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
     % Production Notes
     % [your name here]
     %
     % [your notes here]
     %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

   block at the beginning of the document, just before the ``\documentclass`` declaration.


   #. TODO: PAPER CITATION 1 and 2

      In these two places, fill the missing numbers in the citation header::

      \rhead{\small \href{https://scipost.org/SciPostPhys.?.?.???}{SciPost Phys. ?, ??? (20??)}}


      The first argument of the ``href`` is the simple permanent URL for the publication. This includes 3 numbers: the volume number, issue, and three-digit paper number, for example ``SciPostPhys.1.2.011``. At this stage, leave the paper number to ``???``: this number will be assigned and filled in in the last stage of production.

      The second argument to the ``href`` uses the simple citation, dropping the issue number, for example ``SciPostPhys. 1, 011 (2016)``.


   #. TODO: PACKAGES

      The ``SciPost.cls`` (v1b) class definition requires the following packages:

      * amsmath [NOTE: amsmath, amssymb are redundant and clash with mathdesign]
      * cite
      * doi
      * fancyhdr
      * geometry
      * graphicx
      * hyperref
      * inputenc
      * lineno [for proofs only]
      * titlesec
      * tocloft, nottoc,notlot,notlof
      * xcolor

      If the authors are using extra packages not already in the list above,
      you should paste their list within this TODO block.

      Any package originally included by the authors which you do **not**
      include should be commented out with a  ``% REMOVED IN PROD``
      comments prepended.


   #. TODO: COMMANDS

      If the authors have redefined commands, paste the redefinitions in this block.


   #. Removal of extras

      Strip out other size, length etc. redefinitions by the authors.

      Remove any ``\date``.


   #. TODO: TITLE

      The title is enclosed in::

	\begin{center}{\Large \textbf{\color{scipostdeepblue}{
	[title]
	}}}\end{center}

      Paste the title in this block. If the title is multiline, end it with ``\\``
      in order to ensure proper uniform spacing between the lines.


   #. TODO: AUTHORS

      Put the author names in textbf. No ``comma`` but rather an ``and`` before
      the last author. If multiple authors and affiliations, use ``\textsuperscript``
      and positive integer labels, with a ``*`` for the corresponding author.


   #. TODO: AFFILIATIONS

      If there are many affiliations, each is prepended by the appropriate
      ``{\bf [nr]}\ ``. Separate affiliations ``\\``.

      Put a ``\\[\baselineskip]`` after the affiliations.


   #. TODO: EMAIL (OPTION)

      Optionally, provide the email of the corresponding author using::

	``\href{mailto:[email]}{\small \sf [email]}``

      prepended with ``*`` if corresponding author. If a web link is offered,
      use the format ``{\small \url{[url]}}``.


   #. TODO: ABSTRACT

      Paste the abstract in the provided block::

	\section*{\color{scipostdeepblue}{Abstract}}
	{\bf
	[abstract]
	}


   #. TODO: TOC

      As a general guideline, the paper should contain a table of contents
      if it has more than 6 pages.


   #. TODO: COPYRIGHT

      Include the first author's initials and family name in the copyright
      statement.


   #. TODO: DATES

      Fill in the appropriate received and accepted dates in
      format ``DD-MM-YYYY``. The published date will be filled in later on.


   #. TODO: DOI

      Provide the volume and issue numbers (two places) in the DOI specifier.
      The paper number will be assigned in the final stage of production.


   #. TODO: LINENO

      During proofs stage, activate line numbers.


   #. TODO: CONTENTS

      Paste the entire bulk of the paper in this block,
      including all sections and eventual appendices.


   #. TODO: BIBNR

      If the bibliography contains more than 100 entries, use
      ``999`` instead of ``99`` in the ``\begin{thebibliotraphy}{[nr]}``
      statement.


   #. TODO: BBL

      The references are explicitly pasted into this block.
      If BiBTeX was used, the contents of the ``.bib`` file are pasted here.


Problems
~~~~~~~~

   * package ``lineno`` and ``amsmath`` are incompatible

     Problem: line numbers don't appear when paragraph is followed by align etc.

     Solution: [from `this link <http://phaseportrait.blogspot.nl/2007/08/lineno-and-amsmath-compatibility.html>`_]: paste this in the preamble::

       {\small
       \begin{verbatim}
       %% Patch lineno when used with amsmaths
       \newcommand*\patchAmsMathEnvironmentForLineno[1]{%
       \expandafter\let\csname old#1\expandafter\endcsname\csname #1\endcsname
       \expandafter\let\csname oldend#1\expandafter\endcsname\csname end#1\endcsname
       \renewenvironment{#1}%
       {\linenomath\csname old#1\endcsname}%
       {\csname oldend#1\endcsname\endlinenomath}}%
       \newcommand*\patchBothAmsMathEnvironmentsForLineno[1]{%
       \patchAmsMathEnvironmentForLineno{#1}%
       \patchAmsMathEnvironmentForLineno{#1*}}%
       \AtBeginDocument{%
       \patchBothAmsMathEnvironmentsForLineno{equation}%
       \patchBothAmsMathEnvironmentsForLineno{align}%
       \patchBothAmsMathEnvironmentsForLineno{flalign}%
       \patchBothAmsMathEnvironmentsForLineno{alignat}%
       \patchBothAmsMathEnvironmentsForLineno{gather}%
       \patchBothAmsMathEnvironmentsForLineno{multline}%
       }
       %% End patch lineno


   * Breaking of in-line math equations

     Simply prevent by forcing equations into a math atom by surrouding them with braces,::

       \begin{verbatim}
       Here is an equation that shouldn't be broken: ${E=mc^2}$.
       \end{verbatim}


   * package ``MnSymbol`` is problematic and clashes with amsmath.

     One solution is to import individual symbols according to these
     `instructions <http://tex.stackexchange.com/questions/36006/importing-single-symbol-from-mnsymbol>`_.


References formatting
~~~~~~~~~~~~~~~~~~~~~

   References should be in the following format:

   Things to ensure:

      * Author names are in comma-separated list with format [initials] [last name].

      * Titles are in italics, and capitalization is displayed (using *e.g.* \{\{ [title] \}\} in BiBTeX). For PRL: nouns capitalized.

      * Journal names are abbreviated.

      * Volume number is in bold.

      * Year is in parentheses.

      * Commas separate all elements.

      * All doi are present and displayed in format doi:[doi].

      * The reference is closed by a ``.``




Proofs
------

   * Once the paper has been properly formatted, the ``.tex`` and ``.pdf`` files
     should be copied into new files carrying the ``_proofs_v[nr]`` suffix,
     for example ``SciPost_Phys_1699_9999v9_Bee_proofs_v1.tex``.

   * The ``.pdf`` proofs should be email to the authors for verification.
     Authors should return either an annotated pdf or a list of corrections
     by plain text email.

   * Any modifications should be implemented directly in the main ``.tex`` file.

   * If any further check by the authors are required, start this proofs
     todo-list again, increasing the proofs version number.

   * Once the authors have approved the proofs, the paper can be put forward
     to online publication.


Online publication
------------------


Preparation of final version of record
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

   #. Copy the whole paper folder from folder [journal name]/IN\_PRODUCTION \\to [journal name]/Volume\_[volume nr].

   #. Check online to see which paper number is next available.

   #. Rename this folder using the convention [journal name]\_[volume number]([issue number])\_[paper nr].

   #. Within this folder, take the author-accepted version tex file and rename it using the convention [journal name abbrev]\_[volume nr]\_[issue nr]\_[paper nr].tex.

   #. In this tex source, replace the ??? with the 3-digit paper number (6 places: 4 in preamble, 2 in copyright statement).

   #. Ensure that the author names are in format A. Bee, C. Dee and E. Final.

   #. Insert the correct Received, Accepted and Published dates in copyright statement.

   #. Make sure linenumbers are deactivated.

   #. Does the table of contents (if present) look OK? (Beware of hanging closing line pushed to top of second page.)

   #. If the author-accepted proofs version used BiBTeX, copy the contents of the bbl file into the .tex file, so that BiBTeX is not needed anymore.

   #. Manually correct any incorrect references.

      For arXiv entries, use the format ``\href{https://arxiv.org/abs/####.#####}{arXiv:####.#####}``, and remove any ``(YEAR)``.

      J. Stat. Mech. is annoying (volume number is year). Manually remove volume nr for these, so the format becomes ``A. Bee, \emp{Bee's nice paper}, J. Stat. Mech.: Th. Exp. P##### (20##), \doi{10...}.``

   #. Recompile the LaTeX, and CAREFULLY CHECK EVERYTHING.


Uploading to ``scipost.org``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


   #. From the Submissions Pool, click on the link to initiate the publication process.

   #. Fill in the initiate publication form (using the dates in format YYYY-MM-DD). Submit. You are now on the validate publication page.

   #. Check that the paper number is correct. If not, modify the final tex source to account for this (see previous subsection).

   #. Select who the first author is (if registered as a Contributor; if not, inform the EdAdmin, and choose another author who is registered).

   #. Select the final version's pdf file.

   #. Submit. The paper is now published online.


Metadata preparation and DOI registration with Crossref
-------------------------------------------------------
