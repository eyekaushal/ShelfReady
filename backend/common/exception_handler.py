import logging

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger("shelfready.errors")


class ApiExceptionHandler:
    """
    Makes every API error look the same, so the React app only needs one way to read errors:

        {"error": {"code": "validation_error",
                   "message": "Invalid input.",
                   "details": {"price": ["Must be greater than 0."]}}}
    """

    @classmethod
    def handle(cls, exc, context):
        # Let DRF build its normal response first (it knows the right status codes).
        response = drf_exception_handler(exc, context)

        if response is None:
            # Not a DRF/HTTP error, so a real bug. Log the traceback, hide details from users.
            logger.exception("unhandled error", exc_info=exc)
            return Response(
                cls.build_body("server_error", "Something went wrong. Please try again."),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if isinstance(exc, ValidationError):
            body = cls.build_body("validation_error", "Invalid input.", cls._as_dict(response.data))
        else:
            # e.g. NotAuthenticated → code "not_authenticated", message from DRF.
            body = cls.build_body(cls._code_of(exc), cls._message_of(exc))

        response.data = body
        return response

    @staticmethod
    def build_body(code, message, details=None):
        return {"error": {"code": code, "message": message, "details": details or {}}}

    @staticmethod
    def _code_of(exc):
        # Prefer the specific code on the detail (e.g. simplejwt's "token_not_valid",
        # "no_active_account") over the generic class code ("authentication_failed").
        detail = getattr(exc, "detail", None)
        return getattr(detail, "code", None) or getattr(exc, "default_code", "error")

    @staticmethod
    def _message_of(exc):
        detail = getattr(exc, "detail", None)
        # simplejwt puts the human message under "detail" inside a dict.
        if isinstance(detail, dict) and "detail" in detail:
            return str(detail["detail"])
        return str(detail) if detail is not None else str(exc)

    @staticmethod
    def _as_dict(data):
        # A ValidationError raised with a plain list/string has no field names.
        # Put it under "non_field_errors" so `details` is always a dict.
        if isinstance(data, dict):
            return data
        return {"non_field_errors": data if isinstance(data, list) else [data]}


# DRF settings need a dotted path to a callable, so expose the class method at module level.
handle_exception = ApiExceptionHandler.handle
