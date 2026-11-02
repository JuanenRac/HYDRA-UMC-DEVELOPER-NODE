# =============================================================================
# HYDRA-UMC-DEVELOPER-NODE - src/hydra_umc_developer_node/checkouts.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""A cache of checkouts by revision: git worktrees over a bare mirror kept on this machine.

A remote is cloned once as a bare mirror; each revision a recipe needs becomes a detached worktree named after the commit, so a second
request for the same revision costs nothing and a checkout is always an exact commit, never a moving branch. A revision given as a full
commit hash is verified: if the mirror resolves it to anything else the checkout is refused. Only remotes the configuration lists are
fetched. The cache has a limit in GB that the configuration sets: after each checkout the least recently used worktrees are removed (with
`git worktree remove`) until the cache fits; the mirrors are kept, and a cache that is still over the limit with no worktree left is
reported, never silently ignored.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from .settings import CheckoutSettings

_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
_REV = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,199}$")
_FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
_META = ".dn-meta"


class CheckoutError(ValueError):
    """The checkout is refused or git failed; the text says why."""


def _norm(value: str) -> str:
    return value.replace("\\", "/").rstrip("/")


def remote_allowed(remote: str, allowed: tuple[str, ...]) -> bool:
    """A remote is fetched only when it is exactly a listed one or lies below one (a boundary at a slash)."""
    if not remote or remote.startswith("-"):
        return False
    target = _norm(remote)
    return any(target == _norm(item) or target.startswith(_norm(item) + "/") for item in allowed)


def _git(settings: CheckoutSettings, args: list[str], git_dir: Path | None = None) -> str:
    command = ["git", "-c", "protocol.ext.allow=never"]
    if git_dir is not None:
        command += ["--git-dir", str(git_dir)]
    environment = {key: value for key, value in os.environ.items() if key in ("PATH", "HOME", "USERPROFILE", "SYSTEMROOT", "TEMP", "TMP")}
    environment["GIT_TERMINAL_PROMPT"] = "0"
    try:
        result = subprocess.run(command + args, capture_output=True, text=True, encoding="utf-8", errors="replace",
                                timeout=settings.git_timeout_seconds, env=environment, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise CheckoutError(f"git could not run: {error.__class__.__name__}") from error
    if result.returncode != 0:
        raise CheckoutError("git failed: " + (result.stderr.strip().splitlines() or ["no message"])[-1][:200])
    return result.stdout.strip()


class CheckoutCache:
    def __init__(self, settings: CheckoutSettings, data_dir: Path) -> None:
        self.settings = settings
        self.mirrors = data_dir / settings.mirrors_dir
        self.worktrees = data_dir / settings.worktrees_dir
        self.meta = self.worktrees / _META

    # ------------------------------------------------------------------ mirror and revision
    def ensure_mirror(self, name: str, remote: str) -> Path:
        if not self.settings.enabled:
            raise CheckoutError("checkouts is closed: set checkouts.enabled to true in the configuration file")
        if not _NAME.match(name):
            raise CheckoutError("the name of the checkout is not a plain identifier")
        if not remote_allowed(remote, self.settings.allowed_remotes):
            raise CheckoutError("the remote is not in checkouts.allowedRemotes")
        mirror = self.mirrors / f"{name}.git"
        marker = mirror / "dn-remote"
        if mirror.is_dir():
            if marker.is_file() and marker.read_text(encoding="utf-8").strip() != remote:
                raise CheckoutError("the mirror of this name was made from another remote")
            _git(self.settings, ["fetch", "--prune", "--quiet", "origin"], mirror)
        else:
            self.mirrors.mkdir(parents=True, exist_ok=True)
            _git(self.settings, ["clone", "--mirror", "--quiet", "--", remote, str(mirror)])
            marker.write_text(remote, encoding="utf-8")
        return mirror

    def resolve(self, mirror: Path, rev: str) -> str:
        if not _REV.match(rev):
            raise CheckoutError("the revision is not a plain reference")
        sha = _git(self.settings, ["rev-parse", "--verify", "--quiet", rev + "^{commit}"], mirror)
        if _FULL_SHA.match(rev) and sha != rev:
            raise CheckoutError("the mirror resolves the pinned commit to a different one")
        return sha

    # ------------------------------------------------------------------ worktrees
    def checkout(self, name: str, remote: str, rev: str, now: float | None = None) -> tuple[Path, str]:
        """The worktree of `rev` (an exact commit) and its full hash; fetched and created only when it is not cached yet."""
        mirror = self.ensure_mirror(name, remote)
        sha = self.resolve(mirror, rev)
        target = self.worktrees / f"{name}-{sha[:12]}"
        moment = time.time() if now is None else now
        meta_file = self.meta / f"{target.name}.json"
        if target.is_dir() and meta_file.is_file():
            if _head(self.settings, target) == sha:
                self._touch(meta_file, name, sha, moment)
                return target, sha
            raise CheckoutError("the cached worktree is not at the commit it is named after; remove it and try again")
        if target.exists():
            raise CheckoutError("a folder of that name is in the cache but is not one of ours")
        self.worktrees.mkdir(parents=True, exist_ok=True)
        _git(self.settings, ["worktree", "add", "--detach", "--quiet", str(target), sha], mirror)
        self.meta.mkdir(parents=True, exist_ok=True)
        self._touch(meta_file, name, sha, moment)
        self.prune(protect={target.name})
        return target, sha

    def _touch(self, meta_file: Path, name: str, sha: str, moment: float) -> None:
        meta_file.write_text(json.dumps({"name": name, "sha": sha, "last_used": moment}), encoding="utf-8")

    def entries(self) -> list[dict[str, Any]]:
        found: list[dict[str, Any]] = []
        if not self.meta.is_dir():
            return found
        for meta_file in sorted(self.meta.glob("*.json")):
            try:
                loaded = json.loads(meta_file.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            path = self.worktrees / meta_file.stem
            if isinstance(loaded, dict) and path.is_dir():
                found.append({"dir": meta_file.stem, "name": loaded.get("name"), "sha": loaded.get("sha"),
                              "last_used": float(loaded.get("last_used", 0)), "bytes": directory_size(path)})
        return found

    # ------------------------------------------------------------------ size and limit
    def size_bytes(self) -> int:
        return directory_size(self.mirrors) + directory_size(self.worktrees)

    def over_limit(self) -> bool:
        return self.size_bytes() > self.settings.max_cache_bytes

    def prune(self, protect: set[str] | None = None) -> list[str]:
        """Removes the least recently used worktrees until the cache fits its limit. Returns the folders removed."""
        removed: list[str] = []
        keep = protect or set()
        for entry in sorted(self.entries(), key=lambda item: item["last_used"]):
            if self.size_bytes() <= self.settings.max_cache_bytes:
                break
            if entry["dir"] in keep:
                continue
            self._remove(entry["dir"], str(entry["name"]))
            removed.append(entry["dir"])
        return removed

    def _remove(self, directory: str, name: str) -> None:
        path = (self.worktrees / directory).resolve()
        if self.worktrees.resolve() not in path.parents:
            raise CheckoutError("refusing to remove a folder outside the cache")
        mirror = self.mirrors / f"{name}.git"
        try:
            _git(self.settings, ["worktree", "remove", "--force", str(path)], mirror)
        except CheckoutError:
            shutil.rmtree(path, ignore_errors=True)  # a worktree whose mirror is gone: the folder is still ours (it has a meta file)
        if mirror.is_dir():
            try:
                _git(self.settings, ["worktree", "prune"], mirror)
            except CheckoutError:
                pass
        (self.meta / f"{directory}.json").unlink(missing_ok=True)


def _head(settings: CheckoutSettings, worktree: Path) -> str:
    command = ["git", "-C", str(worktree), "rev-parse", "HEAD"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=settings.git_timeout_seconds, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise CheckoutError(f"git could not run: {error.__class__.__name__}") from error
    return result.stdout.strip()


def directory_size(path: Path) -> int:
    """Bytes of the regular files below `path` (links are not followed); 0 when it does not exist."""
    total = 0
    if not path.is_dir():
        return 0
    for root, _dirs, files in os.walk(path, followlinks=False):
        for file_name in files:
            try:
                full = os.path.join(root, file_name)
                if not os.path.islink(full):
                    total += os.path.getsize(full)
            except OSError:
                continue
    return total
