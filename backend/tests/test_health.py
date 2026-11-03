import pytest


class TestHealth:
    def test_health_returns_ok(self, client):
        response = client.get("/api/health/")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.django_db
class TestDatabaseExtensions:
    def test_vector_and_trigram_are_enabled(self):
        # The 0001 migration must have turned both extensions on.
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("SELECT extname FROM pg_extension")
            names = {row[0] for row in cursor.fetchall()}

        assert {"vector", "pg_trgm"} <= names
