import asyncio
from subprocess import CalledProcessError

import pytest

from foxops.utils import CalledProcessError as FoxopsCalledProcessError
from foxops.utils import check_call


async def test_check_call_should_raise_exception_on_non_zero_exit_code():
    # GIVEN
    program = "false"
    expected_error_msg = r"Command \['false'\] returned non-zero exit status 1\."

    # THEN
    with pytest.raises(CalledProcessError, match=expected_error_msg):
        await check_call(program)


async def test_check_call_should_raise_exception_on_non_zero_exit_code_with_stderr(
    tmp_path,
):
    # GIVEN
    program = "git"
    args = ["status"]
    expected_error_msg = r"not a git repository"

    # THEN
    with pytest.raises(CalledProcessError, match=expected_error_msg):
        await check_call(program, *args, cwd=tmp_path)


async def test_check_call_should_pass_for_zero_exit_code():
    # GIVEN
    program = "true"

    # WHEN & THEN
    await check_call(program)


async def test_check_call_should_forward_args():
    # GIVEN
    program = "echo"
    args = ["Hello", "World"]

    # WHEN
    proc = await check_call(program, *args)

    # THEN
    assert await proc.stdout.read() == b"Hello World\n"


async def test_called_process_error_formats_stderr_under_label(tmp_path):
    with pytest.raises(FoxopsCalledProcessError) as exc_info:
        await check_call("git", "status", cwd=tmp_path)

    msg = str(exc_info.value)
    assert "stderr:\n" in msg
    assert "not a git repository" in msg


async def test_called_process_error_formats_stdout_under_label(tmp_path):
    # `git init` then force a push rejection so git writes to stdout
    script = tmp_path / "fail.sh"
    script.write_text("#!/bin/sh\necho 'output line'\nexit 1\n")
    script.chmod(0o755)

    with pytest.raises(FoxopsCalledProcessError) as exc_info:
        await check_call(str(script))

    msg = str(exc_info.value)
    assert "stdout:\n" in msg
    assert "output line" in msg


def test_called_process_error_decodes_bytes():
    err = FoxopsCalledProcessError(1, ["cmd"], b"out bytes", b"err bytes")
    msg = str(err)
    assert "stdout:\nout bytes" in msg
    assert "stderr:\nerr bytes" in msg


def test_called_process_error_omits_empty_sections():
    err = FoxopsCalledProcessError(1, ["cmd"], b"", b"")
    msg = str(err)
    assert "stdout:" not in msg
    assert "stderr:" not in msg


async def test_check_call_should_kill_process_when_timeout_is_exceeded():
    # GIVEN
    program = "sleep"
    args = ["5"]

    # WHEN & THEN
    with pytest.raises(asyncio.TimeoutError):
        await check_call(program, *args, timeout=0.5)
