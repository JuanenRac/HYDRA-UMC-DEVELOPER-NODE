# =============================================================================
# HYDRA-UMC-DEVELOPER-NODE - src/hydra_umc_developer_node/procs.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""Starting a command with a bound on its time and on its output, and ending it together with the processes it started.

One place for the three runners of this package (the steps of a reproduction, the shared CI validator and the heavy tests): the command
leads its own process group, its output is read while it runs and stops the command when it passes the limit, and when the time is up the
whole tree is ended, so a step that starts a child which sleeps leaves nothing running.
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Bounded:
    """`status` is "ok" (it ended by itself), "timeout" or "over" (it passed the output limit); `output` is the bytes kept."""

    status: str
    returncode: int | None
    output: bytes
    seconds: float


BASE_ENV = ("PATH", "PATHEXT", "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "COMSPEC", "TEMP", "TMP", "TMPDIR", "HOME", "HOMEDRIVE", "HOMEPATH",
            "USERPROFILE", "APPDATA", "LOCALAPPDATA", "LANG", "LC_ALL", "TZ", "PROCESSOR_ARCHITECTURE", "NUMBER_OF_PROCESSORS")
SECRET_WORDS = ("SECRET", "TOKEN", "PASSWORD", "PASSWD", "API_KEY", "APIKEY", "PRIVATE", "CREDENTIAL")


def minimal_environment(extra: tuple[str, ...] = ()) -> dict[str, str]:
    """The environment of a command that runs code of a repository: a short list of names (`BASE_ENV` and `extra`), never a name that looks like a secret."""
    wanted = {name.upper() for name in (*BASE_ENV, *extra)}
    return {key: value for key, value in os.environ.items() if key.upper() in wanted and not any(word in key.upper() for word in SECRET_WORDS)}


def kill_tree(process: subprocess.Popen[bytes]) -> None:
    """Ends the child this module started and the processes it started; nothing else."""
    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, check=False, timeout=30)
        else:
            import signal

            os.killpg(process.pid, signal.SIGKILL)
    except (OSError, ProcessLookupError, subprocess.SubprocessError):
        pass
    try:
        process.kill()
    except OSError:
        pass
    try:
        process.wait(timeout=10)
    except subprocess.SubprocessError:
        pass


def group_options() -> dict[str, Any]:
    """The options of Popen that make the child lead its own process group."""
    if sys.platform == "win32":
        return {"creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)}
    return {"start_new_session": True}


def run_bounded(argv: list[str], cwd: Path | str, env: dict[str, str], timeout: float, max_output_bytes: int) -> Bounded:
    """Runs `argv` with its output (both streams) bounded to `max_output_bytes`, ended with its children when `timeout` seconds pass.

    Raises OSError when the program cannot be started, like subprocess does.
    """
    started = time.monotonic()
    process = subprocess.Popen(argv, cwd=str(cwd), env=env, shell=False, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, **group_options())
    chunks: list[bytes] = []
    state = {"total": 0, "over": False}

    def read() -> None:
        assert process.stdout is not None
        while True:
            block = process.stdout.read(8192)
            if not block:
                return
            state["total"] += len(block)
            if state["total"] > max_output_bytes:
                state["over"] = True
                return
            chunks.append(block)

    reader = threading.Thread(target=read, daemon=True)
    reader.start()
    status = ""
    try:
        deadline = started + timeout
        while process.poll() is None:
            if state["over"]:
                status = "over"
                break
            if time.monotonic() >= deadline:
                status = "timeout"
                break
            time.sleep(0.02)
        if status:
            kill_tree(process)
        else:
            reader.join(timeout=5)
            if state["over"]:
                status = "over"
    except BaseException:
        kill_tree(process)
        raise
    finally:
        reader.join(timeout=2)
        if process.stdout is not None:
            process.stdout.close()
    return Bounded(status or "ok", process.returncode, b"".join(chunks), round(time.monotonic() - started, 2))
