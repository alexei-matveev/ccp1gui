#!/bin/sh


# Make sure we can find python...
which python > /dev/null 2>&1

if [ $? -ne 0 ]; then
echo
echo "############## Error! Cannot find python command #############"
echo
echo "Sorry but the CCP1 GUI cannot run as you do not appear to have"
echo "the python interpreter installed in your path."
echo "Please make sure you have Python installed and that the python"
echo "binary is in your default path."
echo
exit 1
fi

python viewer/main.py $*
