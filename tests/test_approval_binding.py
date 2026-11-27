"""An approval is for one phase on one commit."""

from pathlib import Path

import pytest
from hydra_umc_developer_node import repro
from support import make_repo
from test_repro import NOW, approve, open_settings, prepared, recipe


def test_an_approval_does_not_serve_another_phase_or_commit(tmp_path: Path) -> None:
    store, work = prepared(tmp_path)
    approve(store, recipe())
    for phase, fingerprint in (("after", "sha-a"), ("before", "sha-b")):
        with pytest.raises(repro.ReproError, match="approval"):
            repro.run_recipe(recipe(), store, open_settings(), "c1", phase, work, fingerprint, NOW)
    assert repro.run_recipe(recipe(), store, open_settings(), "c1", "before", work, "sha-a", NOW)["phase"] == "before"


def test_the_switch_off_approves_the_recipe_alone(tmp_path: Path) -> None:
    settings = open_settings(bind_approval_to_revision=False)
    assert repro.approval_digest(recipe(), settings, "after", "x") == repro.approval_digest(recipe(), settings, "before", "y")


def test_every_command_and_folder_is_described() -> None:
    lines = repro.describe({"steps": [{"argv": ["make", "all"], "cwd": "sub"}, {"argv": ["run"]}]})
    assert lines == ['  1. ["make", "all"]  [sub]', '  2. ["run"]  [.]']


def test_the_commit_of_a_work_folder_is_checked(tmp_path: Path) -> None:
    sha = make_repo(tmp_path / "app")
    assert repro.verify_workdir(tmp_path / "app", sha, False) is True
    assert repro.verify_workdir(tmp_path / "app", sha[:10], False) is True
    for wrong in ("0" * 40, "abc"):
        with pytest.raises(repro.ReproError, match="not at the fingerprint"):
            repro.verify_workdir(tmp_path / "app", wrong, True)
    plain = tmp_path / "plain"
    plain.mkdir()
    with pytest.raises(repro.ReproError, match="cannot be read"):
        repro.verify_workdir(plain, sha, False)
    assert repro.verify_workdir(plain, sha, True) is False
