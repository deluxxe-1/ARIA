import asyncio
from pathlib import Path


async def git_status(workspace_root: Path) -> dict[str, str]:
    git_dir = workspace_root / ".git"
    if not git_dir.exists():
        return {"status": "not_repo", "output": "No hay repositorio git en el workspace."}

    try:
        proc = await asyncio.create_subprocess_exec(
            "git",
            "status",
            "--short",
            cwd=workspace_root,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={},
        )
    except FileNotFoundError:
        return {"status": "error", "output": "Git no esta instalado o no se encontro el ejecutable."}
    except PermissionError:
        return {"status": "error", "output": "Permiso denegado al ejecutar git."}

    try:
        stdout_bytes, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=20.0)
    except asyncio.TimeoutError:
        proc.kill()
        try:
            await proc.wait()
        except Exception:
            pass
        return {"status": "error", "output": "Tiempo de espera agotado ejecutando git status."}

    stdout_text = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
    stderr_text = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""
    output = (stdout_text or stderr_text).strip()
    status = "ok" if proc.returncode == 0 else "error"
    return {"status": status, "output": output[:8000]}
