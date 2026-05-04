"""Backstage Essentials Course Builder Toolkit setup.

Run from the toolkit root:
    pip install -e .

This installs the toolkit in editable mode and registers the `bes` command
so it works from any folder on the system.
"""

from setuptools import setup, find_packages

setup(
    name="backstage-essentials-toolkit",
    version="0.1.0",
    description="Reusable toolkit for building Thinkific courses on any subject",
    author="Bill Larsen",
    author_email="bill@backstageessentials.com",
    license="CC BY-NC-SA 4.0",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "click>=8.1",
        "rich>=13.0",
        "pyyaml>=6.0",
        "requests>=2.31",
        "markdown-it-py>=3.0",
        "python-dotenv>=1.0",
    ],
    entry_points={
        "console_scripts": [
            "bes=bes.cli:main",
        ],
    },
    package_data={
        "bes": [],
        "skills": ["**/*"],
        "sync": ["**/*"],
    },
    include_package_data=True,
)
