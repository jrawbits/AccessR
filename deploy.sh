#!/bin/bash

source ../../deploy.sh "$1"
source ../../venv/bin/activate
python endRserve.py  # Won't hurt if it's not running
R CMD Rserve --RS-conf oob.conf
