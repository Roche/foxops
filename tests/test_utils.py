import asyncio
from subprocess import CalledProcessError

import pytest

from foxops.utils import check_call


async def test_check_call_should_raise_exception_on_non_zero_exit_code():
    # GIVEN
    program = "false"
    expected_error_msg = r"Command '\['false'\]' returned non-zero exit status 1. with stdout 'b''' and stderr 'b'''"

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


async def test_check_call_should_kill_process_when_timeout_is_exceeded():
    # GIVEN
    program = "sleep"
    args = ["5"]

    # WHEN & THEN
    with pytest.raises(asyncio.TimeoutError):
        await check_call(program, *args, timeout=0.5)
