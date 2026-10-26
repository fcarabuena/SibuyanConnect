#!/usr/bin/env bash
# Build step for Render (and any Linux host).
set -o errexit

pip install -r requirements.txt
python manage.py compile_translations
python manage.py collectstatic --no-input
python manage.py migrate --no-input
python manage.py setup_roles
