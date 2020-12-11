#!/bin/bash

rm -rf whereithurtsapi/migrations
rm db.sqlite3
python manage.py migrate
python manage.py makemigrations whereithurtsapi
python manage.py migrate whereithurtsapi
python manage.py loaddata whereithurtsapi/fixtures/*.json