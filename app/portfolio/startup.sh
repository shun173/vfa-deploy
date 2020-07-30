#!/bin/sh
uwsgi --socket :8001 --module portfolio.wsgi --py-autoreload 1 --logto /tmp/mylog.log
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic
