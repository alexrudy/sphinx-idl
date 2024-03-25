#
#  setup.py
#  sphinx-idl
#
#  Created by Alexander Rudy on 2014-02-20.
#  Copyright 2014 Alexander Rudy. All rights reserved.
#

from setuptools import setup, find_packages

long_desc = """
This package contains the IDL Sphinx extension.

This extension provides an IDL domain for sphinx

"""

requires = ["Sphinx>=1.0"]

setup(
    name="sphinx-idl",
    version="0.1",
    license="BSD",
    author="Alex Rudy",
    author_email="arrudy@ucsc.edu",
    description='Sphinx "IDL" extension',
    long_description=long_desc,
    zip_safe=False,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Documentation",
        "Topic :: Utilities",
    ],
    platforms="any",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requires,
)
