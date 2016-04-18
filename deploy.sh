#!/bin/bash

# Magic incantation to find directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "Ensuring that NMTK is up to date"
pushd ../..
# source deploy.sh "$1"
source venv/bin/activate # required for python dependencies
popd

echo "Installing R system"
sudo cp $DIR/system/cran.list /etc/apt/sources.list.d/
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E084DAB9
sudo apt-get -y install libcurl4-gnutls-dev libxml2-dev libssl-dev # probably have these already
sudo apt-get -y install r-base r-recommended r-base-dev

echo "Installing required python modules (AccessR)"
pip install --upgrade -r "$DIR/system/requirements.txt" | grep -v up-to-date

echo "Installing required R packages"
sudo su - -c "R --quiet -f $DIR/system/Rpackages.R"

echo "(Re)installing Rserve as a service"
sudo update-rc.d -f Rserve remove
sudo cp $DIR/system/Rserv.conf /etc/Rserv.conf
sudo cp $DIR/system/Rserve.init /etc/init.d/Rserve
sudo chmod 0755 /etc/init.d/Rserve
sudo update-rc.d Rserve defaults 92

echo "(Re)starting Rserve"
sudo service Rserve restart
