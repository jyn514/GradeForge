#!/usr/bin/env python3
import subprocess
from setuptools import setup
from wheel.bdist_wheel import bdist_wheel

with open("README.md") as f:
    long_description = f.read()

with open('requirements.txt') as f:
    requirements = tuple(map(str.strip,
                             filter(lambda s: not s.startswith('#'),
                                    f.readlines())))

class CustomBuild(bdist_wheel):
    def run(self):
        if subprocess.run(['make']).returncode:
            raise RuntimeError("make failed")
        super().run()

setup(name='gradeforge', version='0.0.1-dev',
      description='view available classes for the University of South Carolina',
      author="Joshua Nelson, Brady O'Leary, Charles Daniels, and James Coman",
      author_email='jyn514@gmail.com',
      install_requires=requirements,
      packages=['gradeforge', 'gradeforge.web'],
      long_description=long_description,
      url='https://github.com/jyn514/GradeForge',  # TODO: make a website
      classifiers=(
          'Development Status :: 2 - Pre-Alpha',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Intended Audience :: Education',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 3 :: Only',
          'Topic :: Database',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'
    ),
      entry_points={'console_scripts': ['gradeforge = gradeforge.__main__:main']},
      package_data={'gradeforge': ['classes.sql']},
      cmdclass={'bdist_wheel': CustomBuild}
)
