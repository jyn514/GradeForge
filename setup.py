#!/usr/bin/env python3
from setuptools import setup

with open("README.md") as f:
    long_description = f.read()

setup(name='gradeforge', version='0.0.1',
      description='view available classes for the University of South Carolina',
      author="Joshua Nelson, Brady O'Leary, Charles Daniels, and James Coman",
      author_email='jyn514@gmail.com',
      install_requires=['flask', 'lxml', 'requests'],
      packages=['gradeforge', 'gradeforge.web'],
      long_description=long_description,
      url='https://github.com/jyn514/GradeForge'  # TODO: make a website
)
