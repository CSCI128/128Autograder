# pyright: reportMissingTypeStubs=false
from autograder_platform import __version__

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = '128 Autograder Platform'
copyright = '2025, Gregory Bell'
author = 'Gregory Bell'
release = __version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ['_templates']
exclude_patterns = []
master_doc = "master_toc_tree"


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_book_theme'
html_static_path = ['_static']
html_theme_options = {
    "repository_url": "https://github.com/CSCI128/128Autograder",
    "use_repository_button": True,
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/CSCI128/128Autograder",
            "icon": "fa-brands fa-square-github",
            "type": "fontawesome",
        },
    ],
}

html_logo = "./branding/platform_logo_rectangle.svg"
html_title = "128 Autograder Platform"
html_context = {
    "default_mode": "dark",
}
