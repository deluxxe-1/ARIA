from pathlib import Path
from typing import Any

from app.core.policies import ensure_within_workspace


def list_schema() -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": "list_workspace_files",
            "description": "Lista archivos y carpetas del workspace local.",
            "parameters": {
                "type": "object",
                "properties": {
                    "subpath": {"type": "string", "description": "Subdirectorio dentro del workspace."},
                },
                "required": [],
            },
        },
    }


def read_schema() -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": "read_workspace_file",
            "description": "Lee un archivo de texto dentro del workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Ruta relativa al workspace."},
                },
                "required": ["path"],
            },
        },
    }


async def list_workspace_files(workspace_root: Path, subpath: str = "") -> dict[str, Any]:
    target = ensure_within_workspace(workspace_root, workspace_root / subpath)
    if not target.exists():
        return {"subpath": subpath, "entries": [], "message": "La ruta no existe."}

    entries = [
        {
            "name": item.name,
            "type": "dir" if item.is_dir() else "file",
        }
        for item in sorted(target.iterdir(), key=lambda item: (item.is_file(), item.name.lower()))
    ]
    return {"subpath": subpath, "entries": entries}


async def read_workspace_file(workspace_root: Path, path: str) -> dict[str, Any]:
    target = ensure_within_workspace(workspace_root, workspace_root / path)
    if not target.exists() or not target.is_file():
        return {"path": path, "content": "", "message": "El archivo no existe."}

    return {
        "path": path,
        "content": target.read_text(encoding="utf-8")[:8000],
    }
