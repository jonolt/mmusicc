import setuptools

from mmusicc.version import __version__

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mmusicc-jonolt",
    version=__version__,
    author="Johannes N.",
    author_email="jonolt@mailbox.org",
    description=(
        "A lightweight audio file and metadata control and synchronization "
        "program to transfer the changes made in a master music library to a "
        "derived music library."),
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/jonolt/mmusicc",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Multimedia :: Sound/Audio :: Conversion",
        "Topic :: Multimedia :: Sound/Audio :: Editors",
        "Environment :: Console",
        "Environment :: Console :: Curses",
        "Intended Audience :: End Users/Desktop",
    ],
    python_requires='>=3.5',
    package_data={'mmusicc': ['data/config.yaml']},
    install_requires=['mutagen>=1.43.0', 'PyYAML>=5.3', 'SQLAlchemy>=1.3.0'],
    entry_points={
        "console_scripts": [
            "mmusicc = mmusicc.__main__:main",
        ]
    }
)
