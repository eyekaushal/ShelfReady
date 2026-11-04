from rest_framework import status
from rest_framework.exceptions import APIException


class AIServiceError(APIException):
    """
    Any AI problem we want to show the user as a clean message.

    It's a DRF exception, so ApiExceptionHandler turns it into the standard
    {"error": {"code", "message", "details"}} body. The frontend switches on `code`:

      ai_not_configured  503  no API key set (AI buttons show "AI unavailable")
      ai_busy            503  rate limited / overloaded / timed out: try again soon
      ai_refused         422  Claude declined to read this input
      ai_invalid_output  502  Claude's answer didn't pass our validation, even after a retry
      ai_error           502  anything else from the AI provider
    """

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_code = "ai_error"
    default_detail = "The AI service failed. Please try again or fill the form manually."

    def __init__(self, code: str, message: str, status_code: int = status.HTTP_503_SERVICE_UNAVAILABLE):
        super().__init__(detail=message, code=code)
        self.status_code = status_code
