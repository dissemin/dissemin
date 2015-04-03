#!/bin/sh

echo "### Updating the git repository"
echo "> git checkout master"
git checkout master
echo "> git pull"
git pull
echo "### Logging in as postgres to update the database"
echo "> sudo su postgres"
sudo su postgres << EOF
cd /tmp
wget http://pintoch.ulminfo.fr/latest_dump.gz
echo "### Updating the database…"
cat latest_dump.gz | gunzip | psql dissemin > pull.log 2>&1
rm latest_dump.gz
exit
EOF
echo "### Database updated. The log file is /tmp/pull.log"
echo "### Updating translation files"
echo "> python manage.py compilemessages"
python manage.py compilemessages
echo "### Successfully updated the local copy"

