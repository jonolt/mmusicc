#  Copyright (c) 2020 Johannes Nolte
#  SPDX-License-Identifier: GPL-3.0-or-later

import setuptools


with open("README.rst", "r") as fh:
    long_description = fh.read()

version = {}
with open("./mmusicc/version.py") as fp:
    exec(fp.read(), version)

setuptools.setup(
    name="mmusicc",
    version=version["__version__"],
    author="Johannes Nolte",
    author_email="jonolt@mailbox.org",
    description=(
        "A lightweight audio file and metadata control and synchronization "
        "program to transfer the changes made in a master music library to a "
        "derived music library."
    ),
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/jonolt/mmusicc",
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: POSIX",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Multimedia :: Sound/Audio :: Conversion",
        "Topic :: Multimedia :: Sound/Audio :: Editors",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
    ],
    python_requires=">=3.6",
    package_data={"mmusicc": ["data/config.yaml"]},
    install_requires=["mutagen>=1.41.0", "PyYAML>=3.01", "SQLAlchemy>=1.3.0"],
    entry_points={"console_scripts": ["mmusicc = mmusicc.__main__:main"]},
)
