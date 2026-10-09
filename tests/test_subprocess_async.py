import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.tools import git_tool, shell_tool


class _FakeProc:
    def __init__(self, returncode: int, stdout: bytes, stderr: bytes) -> None:
        self.returncode = returncode
        self._stdout = stdout
        self._stderr = stderr

    async def communicate(self) -> tuple[bytes, bytes]:
        return self._stdout, self._stderr

    async def wait(self) -> int:
        return self.returncode

    def kill(self) -> None:
        self.returncode = -9


@pytest.mark.asyncio
async def test_run_shell_command_disabled_returns_blocked() -> None:
    result = await shell_tool.run_shell_command(Path("/tmp"), "ls", allow_shell=False)
    assert result["status"] == "blocked"


@pytest.mark.asyncio
async def test_run_shell_command_parses_list_args_and_invokes_subprocess_exec(tmp_path: Path) -> None:
    fake_proc = _FakeProc(0, b"hello world\n", b"")
    with patch("app.tools.shell_tool.asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=fake_proc) as m:
        result = await shell_tool.run_shell_command(tmp_path, "ls -la foo", allow_shell=True)
    assert m.await_count == 1
    call_args = m.await_args
    assert call_args is not None
    pos_args = call_args.args
    assert pos_args[:3] == ("ls", "-la", "foo")
    kwargs = call_args.kwargs
    assert "shell" not in kwargs
    assert kwargs.get("cwd") == tmp_path.resolve()
    assert result["status"] == "ok"
    assert "hello world" in result["output"]


@pytest.mark.asyncio
async def test_run_shell_command_handles_timeout(tmp_path: Path) -> None:
    async def long_comm() -> tuple[bytes, bytes]:
        await asyncio.sleep(60)
        return b"", b""

    fake_proc = MagicMock()
    fake_proc.communicate = long_comm
    fake_proc.kill = MagicMock()
    fake_proc.wait = AsyncMock(return_value=-9)

    with patch("app.tools.shell_tool.asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=fake_proc):
        with patch("app.tools.shell_tool.asyncio.wait_for", side_effect=asyncio.TimeoutError()):
            result = await shell_tool.run_shell_command(tmp_path, "sleep 500", allow_shell=True)
    assert result["status"] == "error"
    assert "Tiempo de espera agotado" in result["output"]


@pytest.mark.asyncio
async def test_git_status_subprocess_exec_invoked_as_list(tmp_path: Path) -> None:
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    fake_proc = _FakeProc(0, b" M file.py\n", b"")
    with patch("app.tools.git_tool.asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=fake_proc) as m:
        result = await git_tool.git_status(tmp_path)
    assert m.await_count == 1
    args = m.await_args
    assert args is not None
    assert args.args == ("git", "status", "--short")
    kwargs = args.kwargs
    assert "shell" not in kwargs
    assert result["status"] == "ok"
    assert "M file.py" in result["output"]


@pytest.mark.asyncio
async def test_git_status_not_repo_without_git_dir(tmp_path: Path) -> None:
    result = await git_tool.git_status(tmp_path)
    assert result["status"] == "not_repo"
