#!/bin/bash
sudo cp cran.list /etc/apt/sources.list.d/
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E084DAB9
sudo apt-get -y install libcurl4-gnutls-dev libxml2-dev libssl-dev
sudo apt-get -y install r-base r-recommended r-base-dev
