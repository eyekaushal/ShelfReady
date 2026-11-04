import pytest

from catalog.models import Product

LIST = "/api/products/"


def detail(product_id):
    return f"/api/products/{product_id}/"


def valid_payload(categories, **overrides):
    payload = {
        "name": "Good Day Cashew",
        "brand": "Britannia",
        "category": categories["cream"].id,
        "description": "Cashew cookies.",
        "price": "40.00",
        "image_url": "https://images.example.com/good-day.jpg",
        "gtin": "8901063010574",
        "pack_size": "200 g",
        "variant": "Cashew",
        "tags": ["Cookies", " cashew ", "cookies"],
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
class TestCreate:
    def test_logged_in_user_can_create_and_becomes_owner(self, auth_client, user, categories):
        response = auth_client.post(LIST, valid_payload(categories), format="json")

        assert response.status_code == 201
        body = response.json()
        assert body["created_by"] == "asha"
        assert body["category_detail"]["full_path"] == "Food › Biscuits › Cream Biscuits"
        assert body["tags"] == ["cookies", "cashew"]  # cleaned + de-duplicated
        assert Product.objects.get(pk=body["id"]).created_by == user

    def test_anonymous_cannot_create(self, api_client, categories):
        response = api_client.post(LIST, valid_payload(categories), format="json")

        assert response.status_code == 401

    def test_created_by_in_body_is_ignored(self, auth_client, other_user, categories):
        payload = valid_payload(categories, created_by=other_user.id)

        response = auth_client.post(LIST, payload, format="json")

        assert response.json()["created_by"] == "asha"

    def test_computed_fields_cannot_be_set_or_seen(self, auth_client, categories):
        payload = valid_payload(categories, readiness_score=100, image_phash="abc")

        body = auth_client.post(LIST, payload, format="json").json()

        assert "readiness_score" not in body and "image_phash" not in body
        assert Product.objects.get(pk=body["id"]).readiness_score == 0

    def test_extra_spaces_are_cleaned(self, auth_client, categories):
        payload = valid_payload(categories, name="  Good   Day  ", brand=" Britannia ")

        body = auth_client.post(LIST, payload, format="json").json()

        assert body["name"] == "Good Day"
        assert body["brand"] == "Britannia"


@pytest.mark.django_db
class TestValidation:
    def errors_for(self, client, categories, **overrides):
        response = client.post(LIST, valid_payload(categories, **overrides), format="json")
        assert response.status_code == 400
        error = response.json()["error"]
        assert error["code"] == "validation_error"
        return error["details"]

    @pytest.mark.parametrize("price", ["0", "-5", "0.00"])
    def test_price_must_be_positive(self, auth_client, categories, price):
        details = self.errors_for(auth_client, categories, price=price)

        assert details["price"] == ["Must be greater than 0."]

    def test_price_max_two_decimals(self, auth_client, categories):
        details = self.errors_for(auth_client, categories, price="10.999")

        assert "price" in details

    @pytest.mark.parametrize("url", ["ftp://files.example.com/a.jpg", "javascript:alert(1)", "not a url"])
    def test_image_url_must_be_http_or_https(self, auth_client, categories, url):
        details = self.errors_for(auth_client, categories, image_url=url)

        assert details["image_url"] == ["Enter a valid http or https URL."]

    def test_image_url_is_optional(self, auth_client, categories):
        response = auth_client.post(LIST, valid_payload(categories, image_url=""), format="json")

        assert response.status_code == 201

    def test_name_too_short_and_too_long(self, auth_client, categories):
        assert "name" in self.errors_for(auth_client, categories, name="A")
        assert "name" in self.errors_for(auth_client, categories, name="A" * 201)

    def test_brand_too_long(self, auth_client, categories):
        assert "brand" in self.errors_for(auth_client, categories, brand="B" * 101)

    def test_invalid_gtin(self, auth_client, categories):
        details = self.errors_for(auth_client, categories, gtin="8901063010575")

        assert "check digit" in details["gtin"][0]

    def test_gtin_with_spaces_is_accepted(self, auth_client, categories):
        payload = valid_payload(categories, gtin="8901 0630 1057 4")

        response = auth_client.post(LIST, payload, format="json")

        assert response.json()["gtin"] == "8901063010574"

    def test_duplicate_gtin_is_blocked(self, auth_client, categories):
        auth_client.post(LIST, valid_payload(categories), format="json")

        details = self.errors_for(auth_client, categories, name="Another product")

        assert details["gtin"] == ["A product with this GTIN already exists."]

    def test_many_products_without_gtin_are_fine(self, auth_client, categories):
        first = auth_client.post(LIST, valid_payload(categories, gtin=""), format="json")
        second = auth_client.post(LIST, valid_payload(categories, gtin=""), format="json")

        assert first.status_code == second.status_code == 201

    def test_unknown_category(self, auth_client, categories):
        assert "category" in self.errors_for(auth_client, categories, category=99999)

    def test_required_fields(self, auth_client):
        response = auth_client.post(LIST, {}, format="json")

        details = response.json()["error"]["details"]
        assert {"name", "brand", "category", "description", "price"} <= set(details)

    def test_blank_description(self, auth_client, categories):
        assert "description" in self.errors_for(auth_client, categories, description="   ")


@pytest.mark.django_db
class TestReadUpdateDelete:
    def test_anyone_can_list_and_read(self, api_client, product):
        assert api_client.get(LIST).status_code == 200
        body = api_client.get(detail(product.id)).json()
        assert body["name"] == "Parle-G Gold"

    def test_missing_product_is_404_in_standard_format(self, api_client, db):
        response = api_client.get(detail(99999))

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "not_found"

    def test_owner_can_patch(self, auth_client, product):
        response = auth_client.patch(detail(product.id), {"price": "35.50"}, format="json")

        assert response.status_code == 200
        assert response.json()["price"] == "35.50"

    def test_owner_can_put(self, auth_client, product, categories):
        payload = valid_payload(categories, name="Parle-G Gold Plus")

        response = auth_client.put(detail(product.id), payload, format="json")

        assert response.status_code == 200
        assert response.json()["name"] == "Parle-G Gold Plus"

    def test_updating_own_gtin_is_not_a_duplicate(self, auth_client, product):
        auth_client.patch(detail(product.id), {"gtin": "8901063010574"}, format="json")

        response = auth_client.patch(detail(product.id), {"gtin": "8901063010574"}, format="json")

        assert response.status_code == 200

    def test_owner_can_delete(self, auth_client, product):
        response = auth_client.delete(detail(product.id))

        assert response.status_code == 204
        assert not Product.objects.filter(pk=product.id).exists()


@pytest.mark.django_db
class TestPermissions:
    def test_anonymous_cannot_edit_or_delete(self, api_client, product):
        assert api_client.patch(detail(product.id), {"price": "1"}, format="json").status_code == 401
        assert api_client.delete(detail(product.id)).status_code == 401

    def test_non_owner_cannot_edit_or_delete(self, api_client, other_user, product):
        api_client.force_authenticate(user=other_user)

        patch = api_client.patch(detail(product.id), {"price": "1"}, format="json")
        delete = api_client.delete(detail(product.id))

        assert patch.status_code == delete.status_code == 403
        assert patch.json()["error"]["code"] == "permission_denied"
        assert Product.objects.filter(pk=product.id).exists()

    def test_staff_can_edit_and_delete_any_product(self, api_client, staff_user, product):
        api_client.force_authenticate(user=staff_user)

        assert api_client.patch(detail(product.id), {"price": "31"}, format="json").status_code == 200
        assert api_client.delete(detail(product.id)).status_code == 204
