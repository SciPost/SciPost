.. Howto for publication production

Online Publication
==================

This guide is meant for **Editorial Administrators**. It describes the final publication of manuscripts, after final author proofs approval.

Version: 2017-05-11.


Finalization of manuscript production
-------------------------------------

The steps described here follow up on the :doc:`../production/initial_production` instructions used by production officers.


Preparation of final version of record
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

   #. Copy the whole paper folder from folder [journal name]/IN\_PRODUCTION \\to [journal name]/Volume\_[volume nr].

   #. Check online to see which paper number is next available.

   #. Rename this folder using the convention [journal name]\_[volume number]([issue number])\_[paper nr].

   #. Within this folder, take the author-accepted version tex file and rename it using the convention [journal name abbrev]\_[volume nr]\_[issue nr]\_[paper nr].tex.

   #. In this tex source, replace the ??? with the 3-digit paper number (3 places: 2 in preamble, 1 in copyright statement).

   #. Ensure that the author names are in format Abe Bee, Cee Dee and Elle Fine.

   #. Insert the correct Received, Accepted and Published dates in copyright statement.

   #. Between the ``\begin{minipage}{0.4\textwidth}`` and ``%%%%%%%%%% TODO: DATES`` lines, paste::

	\noindent\begin{minipage}{0.68\textwidth}

   #. Update the DOI block to::

	%%%%%%%%%% TODO: DOI
	}
	\end{minipage}
	\begin{minipage}{0.25\textwidth}
	\begin{center}
	\href{https://crossmark.crossref.org/dialog/?doi=10.21468/SciPostPhys.?.?.???&amp;domain=pdf&amp;date_stamp=20??-??-??}{\includegraphics[width=7mm]{CROSSMARK_BW_square_no_text.png}}\\
	\tiny{Check for}\\
	\tiny{updates}
	\end{center}
	\end{minipage}
	\\\\
	\small{\doi{10.21468/SciPostPhys.?.?.???}
	%%%%%%%%%% END TODO: DOI

   #. In the DOI block you just pasted, make sure the ``?`` are replaced by the
      correct info (DOI (2 places), publication date in format ``YYYY-MM-DD``).

   #. Make sure linenumbers are deactivated, by commenting out the line ``\linenumbers``.

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


Preparation of the JATS version of the abstract
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

   Crossref allows deposit of abstracts using JATS-formatted XML. The ``jats:`` prefix must
   be used by all child elements. Proceed as follows:

   #. Produce the JATS version by converting the LeTeX abstract to JATS using
      ``pandoc`` (see `<https://pandoc.org/index.html>`_), by invoking the command
      ``pandoc -f latex -t jats``, pasting the LaTeX and running pandoc with `Ctrl-D`.

   #. Follow the ``Create/update abstract (JATS version)`` link.

   #. Paste the pandoc output in the Textarea. In the input, add the ``jats:`` prefix
      to all non-MathML elements. For example, the leading ``<p>`` should read
      ``<jats:p>``. Make sure you treat all opening and closing elements.

   #. Submit the form.


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
