.. Howto for publication production

Production of SciPost Publications
==================================

This guide is meant for **Editorial Administrators** and **Production Officers**. It describes the post-acceptance workflow from paper acceptance to publication.

Version: 2017-05-11.


Formatting check
----------------

   If the Submission's references are not properly formatted,
   and/or if these do not include the required DOIs,
   the authors should be emailed and asked to provide them,
   by sending in either an updated ``.bbl`` file or ``.bib`` source.

   Any extra material provided by the authors which supplements
   the arXiv source should be put in a folder ``EXTRA_FROM_AUTH``.


Source retrieval and folder preparation
---------------------------------------

   #. On the SciPost server, navigate to folder
      ``[Journal full name]/IN_PRODUCTION``.
   #. Create a folder
      ``[journal abbrev. name]_[arxiv identifier]_[first author last name]``,
      e.g. ``SciPost_Phys_1604.98141v3_Smart``.
   #. Save the source from arXiv into this folder.
   #. NOTE: the file will be named ``####.#####v#``, which is not recognized
      as a ``.tar.gz`` file on a UNIX system. Rename the file
      ``####.####v#.tar.gz``. Unzip it to produce the folder ``####.#####v#``.
      If this produces another tar file, it is because the submission consists of
      a single ``.tex`` file; you should then rename this to ``####.#####v#.tex``.
   #. Copy the paper’s sources one level down (so from ``####.#####v#`` to
      the current directory). BE CAREFUL: if the authors have included any of
      the SciPost style files (``SciPost.cls``, ``SciPost_bibstyle.bst``), DO NOT
      copy those down. You can skip this step if the previous step immediately led 
      to a ``.tex`` file.
   #. Copy the files in
      ``[Journal full name]/v##_production/FILES_TO_COPY_IN_PAPER_DIR``
      to the current directory. There are 5 files:

         * ``by.eps``
	 * ``logo_scipost_with_bgd.pdf``
	 * ``SciPost_bibstyle.bst``
	 * ``SciPost.cls``
	 * ``SciPost_[Phys, or other as appropriate]_Skeleton.tex``

   #. Copy the skeleton ``.tex`` source to a new file using the name convention
      ``[Journal abbrev. name]_####_#####v#_[first author last name].tex``
      (careful: use underscore instead of . between numbers).


LaTeX file preparation
----------------------

   The next step is to transfer the submission's LaTeX contents into the final file.

   All steps involed appear in the skeleton ``.tex`` source in the form ``%%%%%%%%%% TODO: [TOKEN]`` opening marked, followed by a corresponding ``%%%%%%%%%% END TODO: [TOKEN]`` marker.

   The easiest way to proceed is to copy and paste material from the authors' ``.tex``
   source directly into the (appropriately renamed as per the instructions above)
   skeleton file.

   During the file preparation, if there is anything worth noting about the
   production process, please include this in the::

     %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
     % Production Notes
     % [your name here]
     %
     % [your notes here]
     %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

   block at the beginning of the document, just before the ``\documentclass`` declaration.

   As the person running the production, please identify yourself by writing
   your initials and surname in this block.


General LaTeX tips
~~~~~~~~~~~~~~~~~~

   * Prefer the ``align`` (from package ``amsmath``) environment to ``eqnarray``.
     For a technical discussion, see *e.g.* `this link <http://tug.org/TUGboat/tb33-1/tb103madsen.pdf>`_.

     You do **not** have to systematically replace all ``eqnarray`` with ``align``.
     However, if you do reformat some equations, do shift to ``align``.


Step-by-step procedure
~~~~~~~~~~~~~~~~~~~~~~

   #. TODO: PAPER CITATION

      In this place, fill the missing numbers in the citation header::

      \rhead{\small \href{https://scipost.org/SciPostPhys.?.?.???}{SciPost Phys. ?, ??? (20??)}}


      The first argument of the ``href`` is the simple permanent URL for the publication. This includes 3 numbers: the volume number, issue, and three-digit paper number, for example ``SciPostPhys.1.2.011``. Verify the appropriate issue number (this will be verified later by an EdAdmin). At this stage, leave the paper number to ``???``: this number will be assigned and filled in in the last stage of production.

      The second argument to the ``href`` uses the simple citation, dropping the issue number, for example ``SciPostPhys. 1, 011 (2016)``.


   #. TODO: PACKAGES

      The ``SciPost.cls`` (v1b) class definition requires the following packages:

      * amsmath [NOTE: amssymb is redundant and clashes with mathdesign]
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

      Any package which is added during production should be listed after
      the ``% ADDED IN PRODUCTION`` marker.


   #. TODO: COMMANDS

      If the authors have redefined commands, paste the redefinitions in this block.

      Discard (namely: do not copy and paste) any length (and similar) redefinitions.


   #. TODO: TITLE

      The title is enclosed in::

	\begin{center}{\Large \textbf{\color{scipostdeepblue}{
	[title]
	}}}\end{center}

      Paste the title in this block. End the title with ``\\``
      in order to ensure proper uniform spacing between the lines.


   #. TODO: AUTHORS

      Author names should be in format ``firstname lastname``, e.g. ``John Smith``,
      and should be in textbf. No ``comma`` but rather an ``and`` before
      the last author. If multiple authors and affiliations, use ``\textsuperscript``
      and positive integer labels, with a ``$\star$`` for the corresponding author.
      If multiple email addresses are given, reference them with ``$\dagger$, ...``.


   #. TODO: AFFILIATIONS

      If there are many affiliations, each is prepended by the appropriate
      ``{\bf [nr]}``. Separate affiliations with double-backslash.

      Put a ``\\[\baselineskip]`` after the affiliations.


   #. TODO: EMAIL (OPTION)

      Optionally, provide the email of the corresponding author using::

	``\href{mailto:[email]}{\small \sf [email]}``

      prepended with ``$\star$`` if corresponding author. If no email is to be given,
      comment out the ``$\star$ \href{mailto:[email]}{\small \sf [email]}`` line.

      If a web link is offered, use the format ``{\small \url{[url]}}``.


   #. TODO: ABSTRACT

      Paste the abstract in the provided block::

	\section*{\color{scipostdeepblue}{Abstract}}
	{\bf
	[abstract]
	}


   #. TODO: TOC

      As a general guideline, the paper should contain a table of contents
      if it has more than 6 pages.

      If a TOC should be included, leave the skeleton as it is. If no TOC
      should be there, simply comment out the 2nd and 3rd lines of::

	\vspace{10pt}
	\noindent\rule{\textwidth}{1pt}
	\tableofcontents
	\noindent\rule{\textwidth}{1pt}
	\vspace{10pt}

      explicitly leaving::

	\vspace{10pt}
	%\noindent\rule{\textwidth}{1pt}
	%\tableofcontents
	\noindent\rule{\textwidth}{1pt}
	\vspace{10pt}

      If a single horizontal line is pushed to the next page, correct by
      playing with negatime ``\vspace``.
      

   #. TODO: COPYRIGHT

      Include the first author's initials and family name in the copyright
      statement. If there are just two authors: give both authors' initials
      and last names. If there are more than two authors, use the format
      ``A. Bee {\it et al.}``. Be respectful of any special (non-latin)
      characters in authors' names.


   #. TODO: DATES

      Fill in the appropriate received and accepted dates in
      format ``DD-MM-YYYY``. Be careful to use the correct submission data,
      namely that of the original submission.

      The accepted and published dates will be filled in later on.


   #. TODO: DOI

      Provide the volume and issue numbers (two places) in the DOI specifier.
      The paper number will be assigned in the final stage of production.


   #. TODO: LINENO

      During proofs stage, make sure line numbers are activated (they should
      be by default).


   #. TODO: CONTENTS

      Paste the entire bulk of the paper in this block,
      including all sections and eventual appendices.
      Check that there are no appendices after the references in the
      original tex file.


   #. TODO: BIBNR

      If the bibliography contains more than 100 entries, use
      ``999`` instead of ``99`` in the ``\begin{thebibliotraphy}{[nr]}``
      statement.


   #. TODO: BBL

      The references are explicitly pasted into this block.

      If using BiBTeX, use a ``\bibliography{[bibfilename]}`` command,
      and comment out the ``\begin{thebibliography}`` and ``\end{thebibliography}``
      commands. After running BiBTeX, the contents of the generated
      ``.bib`` file should be pasted in the uncommented ``\begin,\end{thebibliography}``
      block, and the ``\bibliography{[bibfilename]}`` should be commented out.

      *Note: the reason to not use BiBTeX from now on is to easy in-file
      correction of improperly formatted references (instead of having to correct
      the ``.bib`` file)*.


   **You are now ready to typeset the ``.tex`` file**. Simple issues are listed
   below. If you encounter further problems, see the **Problems** list below.

   If you need to run BiBTeX for the references, do so (remembering to do it
   at least twice so the references appear), and then paste the contents of the
   ``.bbl`` file in the ``% TODO: REFERENCES`` block. **Make sure you use the
   correct** ``.bib`` **file**.




Simple issues
~~~~~~~~~~~~~

   * *LaTeX Error: environment acknowledgements undefined* or
     *Undefined control sequence \acknowledgements*

     The users have used ReVTeX; simply change the ``\begin{acknowledgements}``
     or ``\acknowledgements``
     to ``\section*{Acknowledgements}`` (of course also removing any eventual
     ``\end{acknowledgements}``).


   * *LaTeX Error: Environment widetext undefined.*

     The authors have used ReVTeX; simply comment out all ``\begin{widetext}``
     and ``\end{widetext}`` markers.


Problems
~~~~~~~~

   * package ``lineno`` and ``amsmath`` are incompatible

     Problem: line numbers don't appear when paragraph is followed by align etc.

     Solution: [from `this link <http://phaseportrait.blogspot.nl/2007/08/lineno-and-amsmath-compatibility.html>`_]: paste this in the preamble::

       %% Patch lineno when used with amsmath
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

       Here is an equation that should not be broken: ${E=mc^2}$.


   * Equation/table or other text/maths element is just too wide.
     Option: locally change the fontsize by embedding the object in a ``\fontsize`` block,::

       \begingroup
       \fontsize{new font size, e.g. 10pt}{skip, 120% of previous}\selectfont
       [ element]
       \endgroup


   * package ``MnSymbol`` is problematic and clashes with amsmath.

     One solution is to import individual symbols according to these
     `instructions <http://tex.stackexchange.com/questions/36006/importing-single-symbol-from-mnsymbol>`_.


   * Equations spacing in ``align`` environment is too tight.

     The simple solution is to include a spacing specifier of the form ``\nonumber \\[5pt]``,
     where ``5pt`` is a good compromise.

     This spacing can also be set globally by including ``\setlength{\jot}{5pt}`` before the
     ``\begin{document}``.


References formatting
~~~~~~~~~~~~~~~~~~~~~

   References should be in the following format:

      * Author names are in comma-separated list (except for the last author,
	with no comma and an *and*) with format [initials] [last name].

      * Titles are in italics, and capitalization is displayed (using *e.g.* \{\{ [title] \}\} in BiBTeX). For PRL: nouns capitalized.

      * Journal names are abbreviated. A useful resource is this `list of journal abbreviations <http://www.efm.leeds.ac.uk/~mark/ISIabbr/A_abrvjt.html>`_.

      * Volume number is in bold.

      * Issue number can be left out; if included, in parentheses after volume nr.

      * Year is in parentheses.

      * Commas separate all elements.

      * All doi are present and displayed in format doi:[doi]. Note that the doi does
	*not* include any ``http://doi.org`` or similar URL prefix. Instead, it should
	be of the form ``10.###[...]/[...]``.

      * The reference is closed by a ``.``


      For arXiv entries, verify if the paper has been published in the meantime.
      If so, replace this reference with its proper citation.
      If not, use the format ``\href{https://arxiv.org/abs/####.#####}{arXiv:####.#####}``,
      and remove any ``(YEAR)``.

      \J. Stat. Mech. is annoying (volume number is year). Manually remove volume nr for
      these, so the format becomes ``A. Bee, \emp{Bee's nice paper}, J. Stat. Mech.: Th. Exp. [P,L]##### (20##), \doi{10...}.``

      \J. Phys. A is also annoying. Up to and including volume 39 (2006), it's
      \J. Phys. A: Math. Gen. Afterwards, volume 40 (2007) onwards, it's
      \J. Phys. A: Math. Theor.

      Entries in the bibliography which are not references but footnotes,
      should be formatted as such in the main text (using ``\footnote{}``).


      Check that all DOIs work. Remove the ``\meta`` at the end of the bibitem
      if it is present.
    

Layout verification
~~~~~~~~~~~~~~~~~~~

   The whole paper should be scanned through, and the layout of equations
   and figures should be checked and corrected if necessary.

   In particular, the punctuation of equations should be checked and corrected
   if necessary.


Proofs
------

   * Once the paper has been properly formatted, the ``.tex`` and ``.pdf`` files
     should be copied into new files carrying the ``_proofs_v[nr]`` suffix,
     for example ``SciPost_Phys_1699_9999v9_Bee_proofs_v1.tex``.

   * The ``.pdf`` proofs should be emailed to the authors for verification.
     Authors should return either an annotated pdf or a list of corrections
     by plain text email.

   * Any modifications should be implemented directly in the main ``.tex`` file.

   * If any further check by the authors are required, start this proofs
     todo-list again, increasing the proofs version number.

   * Once the authors have approved the proofs, the paper can be put forward
     to online publication.


Online publication
------------------

   These tasks must be performed by an **Editorial Administrator**.


Preparation of final version of record
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

   #. Copy the whole paper folder from folder [journal name]/IN\_PRODUCTION \\to [journal name]/Volume\_[volume nr].

   #. Check online to see which paper number is next available.

   #. Rename this folder using the convention [journal name]\_[volume number]([issue number])\_[paper nr].

   #. Within this folder, take the author-accepted version tex file and rename it using the convention [journal name abbrev]\_[volume nr]\_[issue nr]\_[paper nr].tex.

   #. In this tex source, replace the ??? with the 3-digit paper number (3 places: 2 in preamble, 1 in copyright statement).

   #. Ensure that the author names are in format Abe Bee, Cee Dee and Elle Fine.

   #. Insert the correct Received, Accepted and Published dates in copyright statement.

   #. Make sure linenumbers are deactivated.

   #. Does the table of contents (if present) look OK? (Beware of hanging closing
      line pushed to top of second page). If needed, adjust the ``\vspace`` spacings
      defined around the table of contents, and/or insert an additional ``vspace``
      with negative spacing before the abstract.

   #. If the author-accepted proofs version used BiBTeX, copy the contents of the bbl
      file into the .tex file, so that BiBTeX is not needed anymore.

   #. Verify each reference: authors, title, journal reference, doi link.
      Manually correct any incorrect references.

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

   These tasks must be performed by **Editorial Administrators**,
   who have access to the Publication's editorial tools
   by navigating to the Publication's page.


Author listing
~~~~~~~~~~~~~~

   If not all authors appear in the list presented at the top of the EdAdmin tools,
   these should be added by following the ``Add a missing author`` link.

   The search form can be used to find missing authors who might be
   Registered Contributors. If found, a one-click process adds them.

   You can otherwise create an UnregisteredAuthor object instance and link
   it to the publication, by simply filling in the first and last name fields
   and clicking on ``Add``.


Preparation of the citations list
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

   Follow the ``Create/update citation list metadata`` link.

   In the text area, paste the entire list of bibitems from the paper's
   final ``.tex`` file. Upon clicking on ``Submit``, all DOI entires
   are extracted and formatted into XML metadata which is saved in the
   database.

   Citations with no valid DOI (*e.g.* arXiv preprints, books, etc)
   do not appear in the metadata.


Funding info
~~~~~~~~~~~~

   Following the ``Create/update funding info metadata`` link leads to a
   page where the funding statement of the Publication's ``.tex`` file
   (found either as a separate subsection or in the Acknowledgements)
   can be pasted.


Preparation of the metadata XML
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

   Following the ``Create/update metadata XML`` link auto-generates a
   full XML text field containing all the provided information,
   properly formatted for the upcoming submission to Crossref.

   Verify that the first author is indeed enclosed in a
   ``<person_name sequence='first' contributor_role='author'>`` tag,
   and that subsequent authors (enclosed in
   ``<person_name sequence='additional' contributor_role='author'>`` tags)
   appear in the order of the Publication's author list.

   Once the metadata is set, clicking on ``Accept the metadata``
   saves the metadata to the database and returns one to the Publication's
   page.


Metadata testing and deposit
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

   At this stage, the metadata is ready for uploading to Crossref.
   This occurs via a POST query to either the test or live Crossref server.

   Clicking on ``Test metadata deposit`` immediately posts the metadata
   to the test server, and takes you to a page where the server's
   response headers are displayed. The server also sends a more detailed
   response via email
   (to ``admin@scipost.org``; if you do not have access to this mailbox,
   ask SciPost Administration) with the success status.

   Similarly, the actual deposit is immediately performed upon clicking on the
   ``Deposit the metadata to Crossref``. The response headers are displayed,
   and a detailed email response is sent by Crossref to ``admin@scipost.org``.


   **This completes the publication process.**
