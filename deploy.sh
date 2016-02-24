#!/bin/bash

pushd ../..
source deploy.sh "$1"
source venv/bin/activate
popd

echo "Updating/Installing required python modules (AccessR)."
pip install --upgrade -r requirements.txt|grep -v up-to-date

echo "Restarting Rserve"
python endRserve.py  # Won't hurt if it's not running
R CMD Rserve --RS-conf oob.conf
