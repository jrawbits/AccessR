#!/bin/bash
# Stop the supporting daemons
sudo service celeryd-nmtk stop
sudo service apache2 graceful # restart unobtrusively
# Truncate the log files
sudo truncate -s 0 /var/www/nmtk/logs/access.log
sudo truncate -s 0 /var/www/nmtk/logs/error.log
sudo truncate -s 0 /var/www/nmtk/logs/django-debug.log
sudo truncate -s 0 /var/www/nmtk/logs/django-request.log
sudo truncate -s 0 /var/www/nmtk/logs/celeryd-nmtk.log
# Wait for celeryd to be done
sleep 12
# Restart task queue (celery)
sudo service celeryd-nmtk start
# Python tasks: recollect static, rediscover tools, then close and restart Rserve
source ../../venv/bin/activate
pushd ..
python manage.py collectstatic
python manage.py discover_tools
popd
python endRserve.py # No error if Rserve not running
# Run Rserve from the command line without redirect to debug
R CMD Rserve --RS-conf oob.conf > /dev/null
