from pathlib import Path

import pytest
from app.core.errors import WorkspaceBoundaryError
from app.core.policies import ensure_within_workspace


def test_within_workspace_same_root(tmp_path: Path) -> None:
    result = ensure_within_workspace(tmp_path, tmp_path)
    assert result == tmp_path.resolve()


def test_within_workspace_nested(tmp_path: Path) -> None:
    nested = tmp_path / "a" / "b" / "c.txt"
    nested.parent.mkdir(parents=True, exist_ok=True)
    nested.write_text("hi")
    result = ensure_within_workspace(tmp_path, nested)
    assert result == nested.resolve()


def test_outside_workspace_raises(tmp_path: Path) -> None:
    sibling = tmp_path.parent / "sibling_dir"
    with pytest.raises(WorkspaceBoundaryError):
        ensure_within_workspace(tmp_path, sibling)


def test_path_traversal_raises(tmp_path: Path) -> None:
    evil = tmp_path / ".." / "outside.txt"
    with pytest.raises(WorkspaceBoundaryError):
        ensure_within_workspace(tmp_path, evil)


def test_absolute_path_outside_raises(tmp_path: Path) -> None:
    outside = Path("/tmp") if Path("/tmp").exists() else Path.cwd().parent / "aria_test_outside"
    with pytest.raises(WorkspaceBoundaryError):
        ensure_within_workspace(tmp_path, outside)
