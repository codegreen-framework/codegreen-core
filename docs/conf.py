# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html


import os
import sys

sys.path.insert(0, os.path.abspath("../"))  # Adjust the path to your package location

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "codegreen_core"
copyright = "2025, Dr. Anne Hartebrodt"
author = "Dr. Anne Hartebrodt"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration


templates_path = ["_templates"]
exclude_patterns = []


autodoc_mock_imports = [
    "redis",
    "pandas",
    "entsoe",
    "dateutil",
    "tensorflow",
    "numpy",
    "sklearn",
    "matplotlib",
]

extensions = [
    "sphinx.ext.autodoc",
    "docs._extensions.country_table_extension",
    "sphinx.ext.mathjax",
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["_static"]
html_css_files = ["custom.css"]

html_theme_options = {
    "github_user": "codegreen-framework",
    "github_repo": "codegreen-core"
}

# import codegreen_core
