import logging
import re
import time
import uuid

from common.log.request_context import RequestContext

logger = logging.getLogger("shelfready.request")

# Only accept short, safe ids from the client, so nobody can inject junk into our logs.
_SAFE_ID = re.compile(r"^[A-Za-z0-9-]{1,64}$")


class RequestIdMiddleware:
    """
    Gives every request an id, returns it in the `X-Request-ID` response header,
    and logs one line per request (method, path, status, duration).

    If a user reports a bug, the id in the response header leads straight to the logs.
    """

    HEADER = "X-Request-ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = self._pick_request_id(request)
        RequestContext.set_request_id(request_id)
        request.request_id = request_id

        started = time.perf_counter()
        response = self.get_response(request)
        duration_ms = round((time.perf_counter() - started) * 1000, 1)

        response[self.HEADER] = request_id
        logger.info(
            "request finished",
            extra={
                "method": request.method,
                "path": request.path,  # path only: query strings may contain user text
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response

    def _pick_request_id(self, request) -> str:
        incoming = request.headers.get(self.HEADER, "")
        if _SAFE_ID.match(incoming):
            return incoming
        return uuid.uuid4().hex
