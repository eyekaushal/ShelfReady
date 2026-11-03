from django.http import JsonResponse

from common.exception_handler import ApiExceptionHandler


class ErrorViews:
    """
    JSON versions of Django's 404 and 500 pages.

    DRF errors already go through ApiExceptionHandler. These cover requests that never
    reach a DRF view (e.g. an unknown URL), so the API never answers with an HTML page.
    """

    @staticmethod
    def not_found(request, exception=None):
        body = ApiExceptionHandler.build_body("not_found", "Not found.")
        return JsonResponse(body, status=404)

    @staticmethod
    def server_error(request):
        body = ApiExceptionHandler.build_body("server_error", "Something went wrong. Please try again.")
        return JsonResponse(body, status=500)
