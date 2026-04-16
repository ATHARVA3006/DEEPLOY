#!/bin/bash
pip install -r requirements.txt
cd codeshare
python manage.py collectstatic --noinput
