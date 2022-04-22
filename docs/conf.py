__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
import django
import sphinx_rtd_theme

sys.path.insert(0, os.path.abspath("../scipost_django"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SciPost_v1.settings.empty")

django.setup()

# -- Project information -----------------------------------------------------

project = "SciPost"
copyright = "SciPost Foundation, Jean-Sébastien Caux and other contributors"
author = "Jean-Sébastien Caux"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    "sphinx_rtd_theme",
    "sphinxcontrib.mermaid",
]

autodoc_member_order = "bysource"

mermaid_version = ""
html_js_files = [
   'js/mermaid.js',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]


# The master toctree document.
master_doc = "index"


# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

html_theme_options = {
    "logo_only": True,
    "prev_next_buttons_location": "both",
    "navigation_depth": -1,
    "style_nav_header_background": "#002b49",
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
html_css_files = ["css/scipost_docs.css"]
html_logo = "_static/logo_scipost_RGB_HTML.png"

html_sidebars = {
    "**": ["globaltoc.html", "localtoc.html", "relations.html", "searchbox.html"]
}


# -- Options for LaTeX output ------------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',
    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',
    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',
    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (
        master_doc,
        "SciPost.tex",
        "SciPost Documentation",
        "Jean-Sébastien Caux",
        "manual",
    ),
]


# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [(master_doc, "scipost", "SciPost Documentation", [author], 1)]


# -- Options for Texinfo output ----------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        master_doc,
        "SciPost",
        "SciPost Documentation",
        author,
        "SciPost",
        "SciPost publication portal codebase documentation.",
        "Miscellaneous",
    ),
]


# -- Extension configuration -------------------------------------------------

# -- Options for todo extension ----------------------------------------------

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True


def autodoc_skip_member(app, what, name, obj, skip, options):
    exclusions = [
        "secrets",
        "get_secret",  # remove secrets import
        "migrations",
        "queryset",  # to prevent evaluation of the querysets for DRF-derived CBVs
    ]
    exclude = name in exclusions
    return skip or exclude


def setup(app):
    app.connect("autodoc-skip-member", autodoc_skip_member)
