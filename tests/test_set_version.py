"""scripts/set_version.py must update pyproject.toml and uv.lock together, or neither."""

import runpy
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "set_version.py"


def run(version: str, cwd: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(cwd)
    monkeypatch.setattr("sys.argv", ["set_version.py", version])
    runpy.run_path(str(SCRIPT), run_name="__main__")


def test_updates_both_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    shutil.copy(ROOT / "pyproject.toml", tmp_path)
    shutil.copy(ROOT / "uv.lock", tmp_path)
    run("9.8.7", tmp_path, monkeypatch)
    assert 'version = "9.8.7"' in (tmp_path / "pyproject.toml").read_text()
    assert 'name = "testcontainers-floci"\nversion = "9.8.7"' in (tmp_path / "uv.lock").read_text()


def test_rejected_lock_leaves_both_files_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shutil.copy(ROOT / "pyproject.toml", tmp_path)
    (tmp_path / "uv.lock").write_text("version = 1\n")  # no testcontainers-floci entry
    before = (tmp_path / "pyproject.toml").read_text()
    with pytest.raises(SystemExit):
        run("9.8.7", tmp_path, monkeypatch)
    assert (tmp_path / "pyproject.toml").read_text() == before
    assert (tmp_path / "uv.lock").read_text() == "version = 1\n"
