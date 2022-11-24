#!/usr/bin/env bash
pip install -r requirements.txt

cd mysite
python manage.py collectstatic --no-input
python manage.py migrate
