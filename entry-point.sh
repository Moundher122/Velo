#!/bin/bash

uv run manage.py makemigrations users orders catalog cart
uv run manage.py migrate --noinput
echo "create superuser if missing"
uv run manage.py createsuperuserifmissing
echo "Migrations completed successfully!"
uv run uvicorn velo.asgi:application --host 0.0.0.0 --port 8000 