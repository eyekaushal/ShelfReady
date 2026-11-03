"""
Turns on the two Postgres extensions the catalog needs:

- vector  (pgvector): stores text embeddings and finds look-alike product names
- pg_trgm (trigrams): fuzzy name matching, the fallback when embeddings are off

Doing this in a migration (not by hand) means local Docker, CI and Neon
all get exactly the same database setup from `python manage.py migrate`.
"""

from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations
from pgvector.django import VectorExtension


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        VectorExtension(),
        TrigramExtension(),
    ]
