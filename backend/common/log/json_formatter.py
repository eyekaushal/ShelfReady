import json
import logging
from datetime import UTC, datetime

# Attributes every LogRecord has. Anything else was passed by us via `extra={...}`.
_STANDARD_ATTRS = set(vars(logging.makeLogRecord({}))) | {"message", "asctime", "request_id"}


class JsonFormatter(logging.Formatter):
    """
    Turns each log record into one JSON line, e.g.
    {"time": "...", "level": "INFO", "logger": "...", "request_id": "...", "message": "...",
     "status": 200}

    One JSON object per line is easy to search and filter in Render's log viewer.
    """

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "time": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "message": record.getMessage(),
        }
        # Add our own fields from logger.info("...", extra={"status": 200}).
        for key, value in vars(record).items():
            if key not in _STANDARD_ATTRS:
                entry[key] = value
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        # default=str so values like Decimal or datetime never crash logging.
        return json.dumps(entry, default=str)
