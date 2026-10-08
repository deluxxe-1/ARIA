from pathlib import Path

from app.core.errors import WorkspaceBoundaryError


def ensure_within_workspace(workspace_root: Path, target: Path) -> Path:
    workspace_root = workspace_root.resolve()
    target = target.resolve()

    if workspace_root not in target.parents and target != workspace_root:
        raise WorkspaceBoundaryError("La ruta solicitada esta fuera del workspace permitido.")

    return target
