from pathlib import Path

import pytest
from hydra_umc_developer_node.checkouts import CheckoutCache, CheckoutError, directory_size, remote_allowed
from hydra_umc_developer_node.settings import CheckoutSettings
from support import git, make_repo


def cache_for(tmp_path: Path, remote: Path, **kw: object) -> CheckoutCache:
    options: dict[str, object] = {"enabled": True, "allowed_remotes": (str(remote.parent),)}
    options.update(kw)
    return CheckoutCache(CheckoutSettings(**options), tmp_path / "data")  # type: ignore[arg-type]


def test_remote_allow_list_has_a_boundary_at_a_slash() -> None:
    allowed = ("/srv/repos", "https://example.invalid/org")
    assert remote_allowed("/srv/repos/a", allowed)
    assert remote_allowed("/srv/repos", allowed)
    assert remote_allowed("https://example.invalid/org/x.git", allowed)
    assert not remote_allowed("/srv/repos-evil/a", allowed)
    assert not remote_allowed("--upload-pack=x", allowed)
    assert not remote_allowed("", allowed)
    assert not remote_allowed("/srv/repos/a", ())


def test_closed_by_default(tmp_path: Path) -> None:
    cache = CheckoutCache(CheckoutSettings(), tmp_path)
    with pytest.raises(CheckoutError, match="closed"):
        cache.checkout("x", "/srv/x", "main")


def test_a_remote_outside_the_list_is_refused(tmp_path: Path) -> None:
    remote = tmp_path / "remotes" / "app"
    make_repo(remote)
    cache = CheckoutCache(CheckoutSettings(enabled=True, allowed_remotes=("/elsewhere",)), tmp_path / "data")
    with pytest.raises(CheckoutError, match="allowedRemotes"):
        cache.checkout("app", str(remote), "HEAD")


def test_a_revision_gives_an_exact_worktree_that_is_reused(tmp_path: Path) -> None:
    remote = tmp_path / "remotes" / "app"
    sha = make_repo(remote)
    cache = cache_for(tmp_path, remote)
    path, found = cache.checkout("app", str(remote), "HEAD", now=100.0)
    assert found == sha and (path / "a.txt").read_text(encoding="utf-8").strip() == "one"
    assert path.name == f"app-{sha[:12]}"
    again, same = cache.checkout("app", str(remote), sha, now=200.0)
    assert (again, same) == (path, sha)
    assert cache.entries()[0]["last_used"] == 200.0


def test_a_pinned_commit_that_does_not_exist_is_refused(tmp_path: Path) -> None:
    remote = tmp_path / "remotes" / "app"
    make_repo(remote)
    cache = cache_for(tmp_path, remote)
    with pytest.raises(CheckoutError):
        cache.checkout("app", str(remote), "0" * 40)
    with pytest.raises(CheckoutError, match="plain reference"):
        cache.checkout("app", str(remote), "--help")


def test_a_new_commit_is_fetched_into_the_same_mirror(tmp_path: Path) -> None:
    remote = tmp_path / "remotes" / "app"
    first = make_repo(remote)
    cache = cache_for(tmp_path, remote)
    cache.checkout("app", str(remote), first)
    (remote / "a.txt").write_text("two\n", encoding="utf-8")
    git("commit", "-q", "-am", "second", cwd=remote)
    second = git("rev-parse", "HEAD", cwd=remote)
    path, found = cache.checkout("app", str(remote), "HEAD")
    assert found == second and (path / "a.txt").read_text(encoding="utf-8").strip() == "two"
    assert len(cache.entries()) == 2


def test_the_mirror_of_a_name_cannot_be_pointed_at_another_remote(tmp_path: Path) -> None:
    one, two = tmp_path / "remotes" / "one", tmp_path / "remotes" / "two"
    make_repo(one)
    make_repo(two, {"b.txt": "b\n"})
    cache = cache_for(tmp_path, one)
    cache.checkout("app", str(one), "HEAD")
    with pytest.raises(CheckoutError, match="another remote"):
        cache.checkout("app", str(two), "HEAD")


def test_the_cache_limit_removes_the_least_recently_used_worktree(tmp_path: Path) -> None:
    remote = tmp_path / "remotes" / "app"
    first = make_repo(remote, {"a.txt": "x" * 5000})
    cache = cache_for(tmp_path, remote, max_cache_gb=1.0)
    old_path, _ = cache.checkout("app", str(remote), first, now=100.0)
    (remote / "a.txt").write_text("y" * 5000, encoding="utf-8")
    git("commit", "-q", "-am", "second", cwd=remote)
    second = git("rev-parse", "HEAD", cwd=remote)
    cache.checkout("app", str(remote), second, now=200.0)
    assert old_path.exists()
    # a limit just above the mirror plus one worktree: the next checkout must evict the oldest one
    tight = cache_for(tmp_path, remote, max_cache_gb=(cache.size_bytes() + 1000) / 1024**3)
    (remote / "a.txt").write_text("z" * 5000, encoding="utf-8")
    git("commit", "-q", "-am", "third", cwd=remote)
    third = git("rev-parse", "HEAD", cwd=remote)
    new_path, _ = tight.checkout("app", str(remote), third, now=300.0)
    assert new_path.exists() and not old_path.exists()
    assert [entry["sha"] for entry in tight.entries()].count(first) == 0
    assert not (tight.meta / f"{old_path.name}.json").exists()


def test_an_impossible_limit_is_reported_not_ignored(tmp_path: Path) -> None:
    remote = tmp_path / "remotes" / "app"
    sha = make_repo(remote)
    cache = cache_for(tmp_path, remote, max_cache_gb=0.000001)
    path, _ = cache.checkout("app", str(remote), sha)
    assert path.exists()  # the checkout just made is protected from its own prune
    assert cache.over_limit()
    assert cache.prune() == [path.name]
    assert cache.over_limit()  # the mirror stays and the cache says so


def test_a_foreign_folder_is_never_removed_or_adopted(tmp_path: Path) -> None:
    remote = tmp_path / "remotes" / "app"
    sha = make_repo(remote)
    cache = cache_for(tmp_path, remote)
    foreign = cache.worktrees / f"app-{sha[:12]}"
    foreign.mkdir(parents=True)
    (foreign / "mine.txt").write_text("keep", encoding="utf-8")
    with pytest.raises(CheckoutError, match="not one of ours"):
        cache.checkout("app", str(remote), sha)
    assert (foreign / "mine.txt").exists()
    assert cache.prune() == []


def test_directory_size(tmp_path: Path) -> None:
    (tmp_path / "f").write_bytes(b"abc")
    assert directory_size(tmp_path) == 3
    assert directory_size(tmp_path / "none") == 0
