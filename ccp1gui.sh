#!/bin/sh
# set up path to the ccp1gui directory and any other modules
# that are not installed into the system python distribution

export PYTHONPATH=/home/psh/ccp1gui
#
python viewer/main.py $*
