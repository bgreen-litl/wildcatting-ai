#!/usr/bin/env python

# Require setuptools. See http://pypi.python.org/pypi/setuptools for
# installation instructions, or run the ez_setup script found at
# http://peak.telecommunity.com/dist/ez_setup.py
from setuptools import setup, find_packages

setup(
    name="wildcatting-ai",
    version="1.5",
    url="http://worldofwildcatting.com/",
    author="Original Wildcatter",
    author_email="unknown@example.org",
    packages=["wcai", "wcdata"],
    test_suite="tests",

    install_requires = [
        "coverage==3.5",
        "nose==1.1.2",
        "PEP8==0.6.1",
        "argparse==1.2.1",
        "wildcatting==1.5",
        "neurolab==0.2.0"
        ],

    entry_points = {
        "console_scripts" : [
            "wcdata = wcdata.control:main",
            "wcai = wcai.control:main"
            ]
        }
    )
