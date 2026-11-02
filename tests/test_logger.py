import structlog

from foxops.logger import build_console_renderer

SENTINEL = "a-local-variable-that-must-not-be-rendered"


def _raise_with_a_local_in_scope() -> None:
    local_variable = SENTINEL  # noqa: F841
    raise RuntimeError("boom")


def _render_exception() -> str:
    renderer = build_console_renderer()
    try:
        _raise_with_a_local_in_scope()
    except RuntimeError:
        return renderer(None, "error", {"event": "something failed", "exc_info": True})

    raise AssertionError("expected _raise_with_a_local_in_scope() to raise")


def test_console_renderer_does_not_render_frame_locals():
    output = _render_exception()

    assert "Traceback (most recent call last)" in output
    assert "RuntimeError: boom" in output
    assert SENTINEL not in output


def test_console_renderer_uses_the_plain_traceback_formatter():
    assert build_console_renderer().exception_formatter is structlog.dev.plain_traceback
