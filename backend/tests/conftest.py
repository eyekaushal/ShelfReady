import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def clear_cache():
    # Throttle counters live in the cache. Clear it so one test's requests
    # never count against the next test's rate limit.
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="asha", email="asha@example.com", password="Shelf-ready-42")


@pytest.fixture
def tokens(api_client, user):
    response = api_client.post(
        "/api/auth/login/", {"username": "asha", "password": "Shelf-ready-42"}, format="json"
    )
    return response.json()
