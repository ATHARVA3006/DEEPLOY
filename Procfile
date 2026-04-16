web: cd codeshare && python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn codeshare.wsgi --bind 0.0.0.0:$PORT
