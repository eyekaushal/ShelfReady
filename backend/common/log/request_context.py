from contextvars import ContextVar


class RequestContext:
    """
    Holds the current request id so any code (views, services, logs) can read it
    without passing `request` around.

    A ContextVar is like a global variable, but each request (thread or async task)
    gets its own value, so two requests at the same time never mix up their ids.
    """

    _request_id: ContextVar[str] = ContextVar("request_id", default="-")

    @classmethod
    def get_request_id(cls) -> str:
        return cls._request_id.get()

    @classmethod
    def set_request_id(cls, request_id: str) -> None:
        cls._request_id.set(request_id)
