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


@pytest.fixture(autouse=True)
def skip_product_analysis(request, monkeypatch):
    # Saving a product downloads its image. Tests must not use the network, so the task is
    # skipped unless a test asks for it with @pytest.mark.real_analysis.
    if not request.node.get_closest_marker("real_analysis"):
        monkeypatch.setattr("catalog.views.product_viewset.analyze_product.delay", lambda *a, **k: None)


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


# --- catalog fixtures ---------------------------------------------------------


@pytest.fixture
def other_user(db):
    return User.objects.create_user(username="vikram", email="vikram@example.com", password="Shelf-ready-42")


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(
        username="admin1", email="admin1@example.com", password="Shelf-ready-42", is_staff=True
    )


@pytest.fixture
def categories(db):
    """Food › Biscuits › Cream Biscuits, plus Beverages."""
    from catalog.models import Category

    food = Category.objects.create(name="Food", slug="food")
    biscuits = Category.objects.create(name="Biscuits", slug="biscuits", parent=food)
    cream = Category.objects.create(name="Cream Biscuits", slug="cream-biscuits", parent=biscuits)
    beverages = Category.objects.create(name="Beverages", slug="beverages")
    return {"food": food, "biscuits": biscuits, "cream": cream, "beverages": beverages}


@pytest.fixture
def product(user, categories):
    from catalog.models import Product

    return Product.objects.create(
        name="Parle-G Gold",
        brand="Parle",
        category=categories["biscuits"],
        description="Glucose biscuits.",
        price="30.00",
        pack_size="100 g",
        created_by=user,
    )


@pytest.fixture
def auth_client(api_client, user):
    """An API client logged in as `user` (the product owner)."""
    api_client.force_authenticate(user=user)
    return api_client
