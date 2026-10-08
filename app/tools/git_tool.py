import subprocess
from pathlib import Path


async def git_status(workspace_root: Path) -> dict[str, str]:
    git_dir = workspace_root / ".git"
    if not git_dir.exists():
        return {"status": "not_repo", "output": "No hay repositorio git en el workspace."}

    completed = subprocess.run(
        "git status --short",
        cwd=workspace_root,
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
