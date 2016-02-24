#!/bin/bash

source ../../deploy.sh "$1"
R CMD Rserve --RS-conf oob.conf
