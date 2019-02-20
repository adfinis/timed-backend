"""Setuptools package definition."""

import codecs
import os
from collections import defaultdict

from setuptools import find_packages, setup

from timed import __version__

with codecs.open("README.md", "r", encoding="UTF-8") as f:
    README_TEXT = f.read()


def find_data(packages, extensions):
    """Find data files along with source.

    :param   packages: Look in these packages
    :param extensions: Look for these extensions
    """
    data = defaultdict(list)
    for package in packages:
        package_path = package.replace(".", "/")
        for dirpath, _, filenames in os.walk(package_path):
            for filename in filenames:
                for extension in extensions:
                    if filename.endswith(".%s" % extension):
                        file_path = os.path.join(dirpath, filename)
                        file_path = file_path[len(package) + 1 :]
                        data[package].append(file_path)
    return data


setup(
    name="timed",
    version=__version__,
    author="Adfinis SyGroup AG",
    author_email="https://adfinis-sygroup.ch/",
    description="Timetracking software",
    long_description=README_TEXT,
    install_requires=(
        "python-dateutil",
        "django>=1.11",
        "django-auth-ldap",
        "django-filter",
        "django-multiselectfield",
        "djangorestframework",
        "djangorestframework-jsonapi",
        "djangorestframework-jwt",
        "psycopg2" "pytz",
        "pyexcel-webio",
        "pyexcel-io",
        "django-excel",
        "pyexcel-ods3",
        "pyexcel-xlsx",
        "pyexcel-ezodf",
        "django-environ",
        "django-money",
        "python-redmine",
    ),
    keywords="timetracking",
    url="https://adfinis-sygroup.ch/",
    packages=find_packages(),
    package_data=find_data(find_packages(), ["txt"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: " "GNU Affero General Public License v3",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.5",
    ],
)
