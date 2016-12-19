.. Howto for publication production

Production of SciPost Publications
==================================

This guide is meant for **Editorial Administrators** and **Production Officers**. It describes the post-acceptance workflow from paper acceptance to publication.


Source retrieval and folder preparation
---------------------------------------

#. On the SciPost server, navigate to folder ``[Journal full name]/IN PRODUCTION``.
#. Create a folder ``[journal abbrev. name]_[arxiv identifier]_[first author last name]``, e.g. ``SciPost_Phys_1604.98141v3_Smart``.
#. Save the source from arXiv into this folder.
#. NOTE: the file will be named ``####.#####v#``, which is not recognized as a ``.tar.gz`` file on a UNIX system.
#. Rename the file ``####.####v#.tar.gz``. Unzipping it produces the folder ``####.#####v#``.
#. Copy the files in ``[Journal full name]/v##_production/FILES_TO_COPY_IN_PAPER_DIR`` to the paper-in-production’s folder. There are 4 files: ``by.eps, logo_scipost_with_bgd.pdf, SciPost_bibstyle.bst, SciPost.cls``.
#. Copy all the paper’s sources one level down (so from ``####.#####v#`` to the current directory).
#. Copy the ``.tex`` source to a new file using the name convention ``[Journal abbrev. name]_####_#####v#_[first author last name].tex`` (careful: use underscore instead of . between numbers).


LaTeX file preparation
----------------------


Handling references
~~~~~~~~~~~~~~~~~~~


Implementing the SciPost style
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~



References validation
---------------------


Proofs
------


Online publication
------------------


Metadata preparation and DOI registration with Crossref
-------------------------------------------------------
