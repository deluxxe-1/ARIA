from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from app.tools import shell_tool


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
async def test_shell_tool_allow_shell_false_returns_blocked_robust() -> None:
    workspace = Path("/tmp")
    commands_to_try = [
        "ls",
        "ls -la /etc",
        "rm -rf /",
        "echo hola > archivo.txt",
    ]
    for cmd in commands_to_try:
        result = await shell_tool.run_shell_command(workspace, cmd, allow_shell=False)
        assert result["status"] == "blocked", f"Se esperaba 'blocked' para comando: {cmd}"
        lowered = result["output"].lower()
        assert "desactivado" in lowered or "bloqueado" in lowered or "shell" in lowered


@pytest.mark.asyncio
async def test_shell_tool_malicious_command_no_shell_true_and_args_are_list(tmp_path: Path) -> None:
    malicious_cmd = "ls; rm -rf /"
    fake_proc = _FakeProc(2, b"", b"argumento invalido: ';'\n")
    with patch(
        "app.tools.shell_tool.asyncio.create_subprocess_exec",
        new_callable=AsyncMock,
        return_value=fake_proc,
    ) as mock_subproc:
        result = await shell_tool.run_shell_command(
            workspace_root=tmp_path,
            command=malicious_cmd,
            allow_shell=True,
        )

    assert mock_subproc.await_count == 1
    call_args = mock_subproc.await_args
    assert call_args is not None
    args_passed = call_args.args
    assert isinstance(args_passed, tuple)
    assert len(args_passed) >= 1
    assert "shell" not in call_args.kwargs
    assert "cwd" in call_args.kwargs
    first_arg = args_passed[0]
    assert isinstance(first_arg, str)
    joined = " ".join(args_passed)
    assert "rm" in joined and "/" in joined and ("ls;" in joined or "ls" in joined)
    assert result["status"] == "error"
    assert result["status"] != "ok"
