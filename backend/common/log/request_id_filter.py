import logging

from common.log.request_context import RequestContext


class RequestIdFilter(logging.Filter):
    """Stamps the current request id onto every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = RequestContext.get_request_id()
        return True  # never drop the record, only enrich it
