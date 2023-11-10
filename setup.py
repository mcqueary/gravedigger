from io import open
from os import path

from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))

# Get the long description from the `README.md` file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="graver",
    version="0.1.0",
    description='A Python module for scraping FindAGrave memorials.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mcqueary/graver",
    author="Larry McQueary",
    author_email="contact@mcqueary.org",
    license="MIT",
    classifiers=[],
    keywords="python findagrave scraper",
    packages=find_packages(exclude=["contrib", "docs", "tests"]),
    install_requires=[],
    extras_require={
        "dev": ["setuptools", "wheel", "twine", "pdoc3"],
        "test": ["tox", "pytest"],
    },
    package_data={},
    data_files=[],
    project_urls={
        "Bug Reports": "https://github.com/mcqueary/graver/issues",
        "Source": "https://github.com/mcqueary/graver",
    },
)
