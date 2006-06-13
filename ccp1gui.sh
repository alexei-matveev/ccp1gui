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

# Work out where the base gui directory is
if [ "${0:0:1}" = "/" ]
then
    # we've been called with an absolute path so just get the directory
    guidir=`dirname $0`
else
    # We've been called with a relative path so work out where the script lives
    # relvative to us, go there and print the directory name to get its full path
    path_to_script=`dirname $0`
    guidir=`(cd $path_to_script; pwd)`
fi


python $guidir/viewer/main.py $*
