import subprocess
from pathlib import Path

from app.core.policies import ensure_within_workspace


async def run_shell_command(workspace_root: Path, command: str, allow_shell: bool) -> dict[str, str]:
    if not allow_shell:
        return {"status": "blocked", "output": "El shell esta desactivado por configuracion."}

    target = ensure_within_workspace(workspace_root, workspace_root)
    completed = subprocess.run(
        command,
        cwd=target,
        capture_output=True,
        text=True,
        shell=True,
        timeout=20,
    )
    output = (completed.stdout or completed.stderr).strip()
    return {
        "status": "ok" if completed.returncode == 0 else "error",
        "output": output[:8000],
    }
