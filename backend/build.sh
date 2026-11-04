#!/usr/bin/env bash
# Render runs this on every deploy. The free plan has no shell, so database setup happens here too.
set -o errexit  # stop at the first failure, so a broken deploy never goes live

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input
python manage.py seed_catalog  # safe to repeat: updates demo rows instead of duplicating them
python manage.py analyze_catalog  # measures only what is missing, then rechecks look-alike pairs
