************************************
Contributing to the SciPost codebase
************************************

Our self-served Git depot at `git.scipost.org <https://git.scipost.org>`_
hosts the `main SciPost repository <https://git.scipost.org/scipost/SciPost>`_
(access credentials required).

Pull requests are admitted from members of our Development Team.
Please conform to all conventions below in any pull request you create.



Coding conventions
==================

Our starting points are the `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`_
specification, and the `Django style <https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/>`_.

We further default to the conventions in Black.

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black

Hereby follow some extra specializations.

To ease your work, if you have an editor with
`EditorConfig <https://editorconfig.org>`_ support,
you can use our ``.editorconfig`` file at the base of the repository.

Line length
-----------
We deviate from `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`_
and set the maximal line length to 88.


Docstrings
----------

Docstrings are in reStructruredText (of course), and should fit within the
allowed line length of 88.


Templates
---------

Indentation
^^^^^^^^^^^

There are no fixed, generally-accepted conventions for indentation in Django templates.

The Django documentation's `Python style <https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/#python-style>`_
paragraph specifies 4 spaces for Python, and 2 spaces for HTML
(note however the amusing fact that the Django docs themselves, when displaying template code,
do not follow this convention and use 4 spaces).

The question remains what to do with template tags. We adopt the convention that

* **template tags should be indented two spaces**, just like HTML elements

For example: please write::

  <div>
    <ul>
      {% for publication in publications %}
        <li>{{ publication }}</li>
      {% endfor %}
    </ul>
  </div>

(2 spaces between HTML tags and/or template tags), instead of::

  <div>
      <ul>
      {% for publication in publications %}
      <li>{{ publication }}</li>
      {% endfor %}
      </ul>
  </div>

in which the following crimes are committed: 4 spaces between HTML tags, no spaces
between HTML and template tags (and their reverse crimes).

Though this means that the rendered HTML will have some extra spaces, who cares?
The source is displayed more nicely, and HTML is space-insensitive (though an evil
hacker would be able to see from the spacings that you did use *some* tags; but which one(s)?).



Curly braces
^^^^^^^^^^^^

Though this is already specified in the Django coding style, we repeat it here to avoid
you the risk of life-threatening injuries. Put one space between braces and tag contents, so::

  {{ publication }}

instead of the harder-to-read::

  {{publication}}
