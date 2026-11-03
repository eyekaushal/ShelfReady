from rest_framework.exceptions import NotAuthenticated, ValidationError

from common.exception_handler import ApiExceptionHandler


class TestApiExceptionHandler:
    def test_validation_error_has_field_details(self):
        exc = ValidationError({"price": ["Must be greater than 0."]})

        response = ApiExceptionHandler.handle(exc, context={})

        assert response.status_code == 400
        assert response.data == {
            "error": {
                "code": "validation_error",
                "message": "Invalid input.",
                "details": {"price": ["Must be greater than 0."]},
            }
        }

    def test_validation_error_without_fields_goes_to_non_field_errors(self):
        response = ApiExceptionHandler.handle(ValidationError("Bad file."), context={})

        assert response.data["error"]["details"] == {"non_field_errors": ["Bad file."]}

    def test_auth_error_uses_drf_code_and_message(self):
        response = ApiExceptionHandler.handle(NotAuthenticated(), context={})

        assert response.status_code == 401
        assert response.data["error"]["code"] == "not_authenticated"
        assert response.data["error"]["details"] == {}

    def test_unexpected_error_becomes_safe_500(self):
        response = ApiExceptionHandler.handle(RuntimeError("secret internals"), context={})

        assert response.status_code == 500
        assert response.data["error"]["code"] == "server_error"
        assert "secret" not in response.data["error"]["message"]


class TestUnknownUrl:
    # pytest-django runs tests with DEBUG=False, like production, so handler404 is used.
    def test_unknown_url_returns_json_404(self, client):
        response = client.get("/api/does-not-exist/")

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "not_found"


class TestDjangoErrorsAreConverted:
    def test_django_http404_gets_not_found_code(self):
        from django.http import Http404

        response = ApiExceptionHandler.handle(Http404(), context={})

        assert response.status_code == 404
        assert response.data["error"]["code"] == "not_found"

    def test_django_permission_denied_gets_code(self):
        from django.core.exceptions import PermissionDenied

        response = ApiExceptionHandler.handle(PermissionDenied(), context={})

        assert response.status_code == 403
        assert response.data["error"]["code"] == "permission_denied"
