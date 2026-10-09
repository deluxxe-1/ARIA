import asyncio
import shlex
from pathlib import Path

from app.core.policies import ensure_within_workspace


async def run_shell_command(workspace_root: Path, command: str, allow_shell: bool) -> dict[str, str]:
    if not allow_shell:
        return {"status": "blocked", "output": "El shell esta desactivado por configuracion."}

    target = ensure_within_workspace(workspace_root, workspace_root)
    try:
        args = shlex.split(command, posix=True)
    except ValueError as exc:
        return {"status": "error", "output": f"Comando invalido: {str(exc)[:8000]}"}

    if not args:
        return {"status": "error", "output": "Comando vacio."}

    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            cwd=target,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={},
        )
    except FileNotFoundError as exc:
        return {"status": "error", "output": f"Ejecutable no encontrado: {str(exc)[:8000]}"}
    except PermissionError as exc:
        return {"status": "error", "output": f"Permiso denegado: {str(exc)[:8000]}"}

    try:
        stdout_bytes, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=20.0)
    except asyncio.TimeoutError:
        proc.kill()
        try:
            await proc.wait()
        except Exception:
            pass
        return {"status": "error", "output": "Tiempo de espera agotado ejecutando el comando."}

    stdout_text = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
    stderr_text = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""
    output = (stdout_text or stderr_text).strip()
    status = "ok" if proc.returncode == 0 else "error"
    return {"status": status, "output": output[:8000]}
