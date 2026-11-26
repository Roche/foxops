import json
from typing import Any

import structlog

from foxops.logger import build_console_renderer, build_renderers

SENTINEL = "a-local-variable-that-must-not-be-rendered"


def _raise_with_a_local_in_scope() -> None:
    local_variable = SENTINEL  # noqa: F841
    raise RuntimeError("boom")


def _render_exception(renderers) -> str:
    try:
        _raise_with_a_local_in_scope()
    except RuntimeError:
        event: Any = {"event": "something failed", "exc_info": True}
        for renderer in renderers:
            event = renderer(None, "error", event)
        return event

    raise AssertionError("expected _raise_with_a_local_in_scope() to raise")


def test_console_renderer_does_not_render_frame_locals():
    output = _render_exception([build_console_renderer()])

    assert "Traceback (most recent call last)" in output
    assert "RuntimeError: boom" in output
    assert SENTINEL not in output


def test_console_renderer_uses_the_plain_traceback_formatter():
    assert build_console_renderer().exception_formatter is structlog.dev.plain_traceback


def test_json_renderer_writes_the_whole_entry_on_one_line():
    output = _render_exception(build_renderers("json"))

    assert "\n" not in output
    entry = json.loads(output)
    assert entry["event"] == "something failed"
    assert "Traceback (most recent call last)" in entry["exception"]
    assert entry["exception"].endswith("RuntimeError: boom")


def test_json_renderer_does_not_render_frame_locals():
    output = _render_exception(build_renderers("json"))

    assert SENTINEL not in output
