import json
import logging

from common.log.json_formatter import JsonFormatter
from common.log.request_context import RequestContext
from common.log.request_id_filter import RequestIdFilter


class TestRequestIdMiddleware:
    def test_response_has_generated_request_id(self, client):
        response = client.get("/api/health/")

        assert len(response["X-Request-ID"]) == 32  # uuid4 hex

    def test_safe_incoming_request_id_is_reused(self, client):
        response = client.get("/api/health/", headers={"X-Request-ID": "abc-123"})

        assert response["X-Request-ID"] == "abc-123"

    def test_unsafe_incoming_request_id_is_replaced(self, client):
        response = client.get("/api/health/", headers={"X-Request-ID": "bad id; DROP TABLE"})

        assert response["X-Request-ID"] != "bad id; DROP TABLE"


class TestJsonLogging:
    def test_log_line_is_json_with_request_id_and_extra_fields(self):
        RequestContext.set_request_id("req-1")
        record = logging.makeLogRecord({"msg": "hello", "levelname": "INFO", "status": 200})
        RequestIdFilter().filter(record)

        entry = json.loads(JsonFormatter().format(record))

        assert entry["message"] == "hello"
        assert entry["request_id"] == "req-1"
        assert entry["status"] == 200
