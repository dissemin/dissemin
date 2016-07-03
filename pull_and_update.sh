#!/bin/sh

# go into directory of script
DIR="$( cd "$( dirname "$0" )" && pwd )"
cd "$DIR"

set -e
echo "### Updating the git repository"
echo "> git checkout master"
git checkout master
echo "> git pull"
git pull
echo "### Updating dependencies ###"
sudo pip install --src .src -r requirements.txt
sudo pip install --src .src -r requirements-dev.txt
echo "### Migrating the database ###"
python manage.py migrate
echo "### Updating translation files"
echo "> python manage.py compilemessages"
python manage.py compilemessages
echo "### Successfully updated the local copy"
echo ""
echo "Now you can run the platform with:"
echo "./launch.sh"
echo ""
echo "It will be available at http://localhost:8000/"
echo ""
