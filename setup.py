#!/usr/bin/env python

"""
This setup.py script seems to suffer from a bug in the function get_data_files:

/usr/lib/python2.4/distutils/command/build_py.py

specifically the line:

plen = len(src_dir)+1

If len(src_dir) is 0, which it is in this case, the first character of the directory gets chopped off.

"""

from distutils.core import setup
import glob
# For Windows builds
#import py2exe

# patch distutils if it can't cope with the "classifiers" or
# "download_url" keywords
from sys import version
if version < '2.2.3':
    from distutils.dist import DistributionMetadata
    DistributionMetadata.classifiers = None
    DistributionMetadata.download_url = None


# Create list of miscellaneous non-python files
#DATA_FILES=[
#    ('',['ccp1gui.bat','ccp1gui.sh','LICENCE','README'])
#    ],
#     ]
SCRIPTS = glob.glob('scripts/*.py')
             

# Call setup to work it's magic
setup(
      name='ccp1gui',
      
      version='0.8',
      
      author='Paul Sherwood, Huub van Dam and Jens Thomas',
      
      author_email='paul.sherwood@stfc.ac.uk',
      
      url='http://www.cse.clrc.ac.uk/qcg/ccp1gui/index.shtml',
      
      description='The CCP1GUI project aims to develop a free, extensible Graphical User Interface to various computational chemistry codes developed by the worldwide academic community, with an emphasis on ab initio Quantum Chemistry codes.',
      
      license='The GNU General Public License (GPL)',
      
      packages=['ccp1gui',
                'ccp1gui.basis',
                'ccp1gui.chempy',
                'ccp1gui.generic',
                'ccp1gui.idle',
                'ccp1gui.interfaces',
                'ccp1gui.jobmanager',
                'ccp1gui.objects',
                'ccp1gui.viewer'],
      
      package_dir = {'ccp1gui': ''},
      
      package_data={'ccp1gui': ['doc/*.txt',
                                'doc/python_style_guide.htm',
                                'doc/html/*.html',
                                'doc/html/images/*.png',
                                'doc/html/images/*.jpg',
                                'examples/*.*',
                                'scripts/*.py'
                                ]},
# console line for py2exe
#      console=['viewer/main.py']
#      scripts=SCRIPTS
#      data_files=DATA_FILES
      )
