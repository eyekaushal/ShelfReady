"""Fakes for the Anthropic SDK and images, so AI tests never call the real API or network."""

import io
import json
from types import SimpleNamespace

from PIL import Image


def png_bytes(width=400, height=400, color="red", image_format="PNG") -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (width, height), color).save(output, format=image_format)
    return output.getvalue()


def claude_response(data=None, *, text=None, stop_reason="end_turn"):
    """Build an object shaped like an SDK BetaMessage."""
    body = text if text is not None else json.dumps(data)
    return SimpleNamespace(
        stop_reason=stop_reason,
        content=[SimpleNamespace(type="text", text=body)],
        usage=SimpleNamespace(input_tokens=1200, output_tokens=150),
        _request_id="req_test_123",
    )


class FakeSDK:
    """Stands in for anthropic.Anthropic(): `.beta.messages.create(**kwargs)` returns queued answers."""

    def __init__(self, *answers):
        self.answers = list(answers)
        self.calls = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer
