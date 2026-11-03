import pytest
from django.contrib.auth.models import User

REGISTER = "/api/auth/register/"
LOGIN = "/api/auth/login/"
REFRESH = "/api/auth/refresh/"
LOGOUT = "/api/auth/logout/"
ME = "/api/auth/me/"

VALID_SIGNUP = {"username": "ravi", "email": "Ravi@Example.com", "password": "Kirana-shelf-99"}


@pytest.mark.django_db
class TestRegister:
    def test_register_creates_user_and_returns_tokens(self, api_client):
        response = api_client.post(REGISTER, VALID_SIGNUP, format="json")

        assert response.status_code == 201
        body = response.json()
        assert body["user"]["username"] == "ravi"
        assert body["user"]["email"] == "ravi@example.com"  # stored lower-case
        assert "password" not in body["user"]
        assert body["access"] and body["refresh"]

    def test_password_is_hashed_not_stored_raw(self, api_client):
        api_client.post(REGISTER, VALID_SIGNUP, format="json")

        user = User.objects.get(username="ravi")
        assert user.password != VALID_SIGNUP["password"]
        assert user.check_password(VALID_SIGNUP["password"])

    def test_duplicate_email_is_rejected_case_insensitively(self, api_client, user):
        data = {**VALID_SIGNUP, "email": "ASHA@example.com"}

        response = api_client.post(REGISTER, data, format="json")

        assert response.status_code == 400
        assert "email" in response.json()["error"]["details"]

    def test_duplicate_username_is_rejected(self, api_client, user):
        data = {**VALID_SIGNUP, "username": "asha"}

        response = api_client.post(REGISTER, data, format="json")

        assert response.status_code == 400
        assert "username" in response.json()["error"]["details"]

    def test_weak_password_uses_standard_error_format(self, api_client):
        data = {**VALID_SIGNUP, "password": "12345678"}

        response = api_client.post(REGISTER, data, format="json")

        assert response.status_code == 400
        error = response.json()["error"]
        assert error["code"] == "validation_error"
        assert "password" in error["details"]

    def test_missing_fields_are_reported(self, api_client):
        response = api_client.post(REGISTER, {}, format="json")

        details = response.json()["error"]["details"]
        assert {"username", "email", "password"} <= set(details)


@pytest.mark.django_db
class TestLogin:
    def test_login_returns_token_pair(self, api_client, user):
        response = api_client.post(
            LOGIN, {"username": "asha", "password": "Shelf-ready-42"}, format="json"
        )

        assert response.status_code == 200
        assert {"access", "refresh"} <= set(response.json())

    def test_wrong_password_returns_401_in_standard_format(self, api_client, user):
        response = api_client.post(LOGIN, {"username": "asha", "password": "wrong"}, format="json")

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "no_active_account"


@pytest.mark.django_db
class TestMe:
    def test_me_requires_login(self, api_client):
        response = api_client.get(ME)

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "not_authenticated"

    def test_me_returns_current_user(self, api_client, tokens):
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

        response = api_client.get(ME)

        assert response.status_code == 200
        assert response.json()["username"] == "asha"

    def test_garbage_token_is_rejected(self, api_client):
        api_client.credentials(HTTP_AUTHORIZATION="Bearer not-a-real-token")

        response = api_client.get(ME)

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "token_not_valid"


@pytest.mark.django_db
class TestRefreshAndLogout:
    def test_refresh_returns_new_tokens(self, api_client, tokens):
        response = api_client.post(REFRESH, {"refresh": tokens["refresh"]}, format="json")

        assert response.status_code == 200
        body = response.json()
        assert body["access"]
        assert body["refresh"] != tokens["refresh"]  # rotation is on

    def test_old_refresh_token_stops_working_after_rotation(self, api_client, tokens):
        api_client.post(REFRESH, {"refresh": tokens["refresh"]}, format="json")

        response = api_client.post(REFRESH, {"refresh": tokens["refresh"]}, format="json")

        assert response.status_code == 401

    def test_logout_blacklists_refresh_token(self, api_client, tokens):
        logout = api_client.post(LOGOUT, {"refresh": tokens["refresh"]}, format="json")
        refresh_after = api_client.post(REFRESH, {"refresh": tokens["refresh"]}, format="json")

        assert logout.status_code == 205
        assert refresh_after.status_code == 401

    def test_logout_twice_is_a_clean_error(self, api_client, tokens):
        api_client.post(LOGOUT, {"refresh": tokens["refresh"]}, format="json")

        response = api_client.post(LOGOUT, {"refresh": tokens["refresh"]}, format="json")

        assert response.status_code == 400
        assert "refresh" in response.json()["error"]["details"]

    def test_logout_without_token_is_validation_error(self, api_client):
        response = api_client.post(LOGOUT, {}, format="json")

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "validation_error"


@pytest.mark.django_db
class TestThrottle:
    def test_login_is_rate_limited(self, api_client):
        bad_login = {"username": "nobody", "password": "wrong"}
        responses = [api_client.post(LOGIN, bad_login, format="json") for _ in range(21)]

        assert responses[-1].status_code == 429
        assert responses[-1].json()["error"]["code"] == "throttled"
