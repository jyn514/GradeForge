#!/usr/bin/env python3
from setuptools import setup

with open("README.md") as f:
    long_description = f.read()

with open('requirements.txt') as f:
    requirements = tuple(map(str.strip,
                             filter(lambda s: not s.startswith('#'),
                                    f.readlines())))

setup(name='gradeforge', version='0.0.1-dev',
      description='view available classes for the University of South Carolina',
      author="Joshua Nelson, Brady O'Leary, Charles Daniels, and James Coman",
      author_email='jyn514@gmail.com',
      install_requires=requirements,
      packages=['gradeforge', 'gradeforge.web'],
      long_description=long_description,
      url='https://github.com/jyn514/GradeForge',  # TODO: make a website
      classifiers=(
          'Development Status::2 - Pre-Alpha',
          'Environment::Console',
          'Environment::Web Environment',
          'Framework::Flask',
          'Intended Audience::Developers',
          'Intended Audience::Education',
          'Intended Audience::End Users/Desktop',
          'Operating System::OS Independent',
          'Programming Language::Python::3::Only',
          'Topic::Database::Front-Ends',
          'Topic::Internet::WWW/HTTP::Dynamic Content'
          # TODO: add license (full list at https://pypi.org/classifiers/)
    ),
      entry_points={'console_scripts': ['gradeforge = gradeforge.__main__']}
)