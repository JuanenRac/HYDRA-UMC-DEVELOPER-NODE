# =============================================================================
# HYDRA-UMC-DEVELOPER-NODE - src/hydra_umc_developer_node/settings.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""The configuration file: every switch and every tuned value of the node.

Everything is closed by default. Each section has an `enabled` switch that must be a real JSON boolean (the text "false" is an error, not
a way to switch something on), a key the node does not know is an error, and a missing file means all defaults, that is, everything closed.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

LANGUAGES = ("en", "es", "de", "fr", "it", "ja", "zh", "pt")
GIB = 1024**3


class SettingsError(ValueError):
    """The configuration file is unreadable or has a value the node refuses."""


@dataclass(frozen=True)
class IngestSettings:
    enabled: bool = False
    max_bundle_bytes: int = 1_000_000
    require_transport_mac: bool = True
    secret_env: str = "HYDRA_UMC_DEVELOPER_NODE_TRANSPORT_SECRET"
    secret_file: str = ""
    expected_to_node: str = "developer-node"
    max_clock_skew_seconds: int = 300
    nonce_retention_seconds: int = 86_400


@dataclass(frozen=True)
class ReproSettings:
    enabled: bool = False
    approval_max_age_minutes: int = 30
    step_timeout_seconds: int = 60
    max_steps: int = 20
    max_output_bytes: int = 65_536
    allowed_commands: tuple[str, ...] = ()


@dataclass(frozen=True)
class CheckoutSettings:
    enabled: bool = False
    mirrors_dir: str = "mirrors"
    worktrees_dir: str = "worktrees"
    max_cache_gb: float = 5.0
    allowed_remotes: tuple[str, ...] = ()
    git_timeout_seconds: int = 120

    @property
    def max_cache_bytes(self) -> int:
        return int(self.max_cache_gb * GIB)


@dataclass(frozen=True)
class PanelSettings:
    enabled: bool = False
    max_journal_entries: int = 200


@dataclass(frozen=True)
class ServerPushSettings:
    """Sending the status document to HYDRA-UMC-SERVER (`panel push`). Off by default; the token of the node is never in this file."""

    enabled: bool = False
    url: str = ""
    node_id: str = ""
    token_env: str = "HYDRA_UMC_DEVELOPER_NODE_TOKEN"
    token_file: str = ""
    timeout_seconds: int = 10


@dataclass(frozen=True)
class EcosystemCiSettings:
    enabled: bool = False
    workspace: str = ""
    repos: tuple[str, ...] = ()
    timeout_seconds: int = 600
    tail_lines: int = 12
    approval_max_age_minutes: int = 30


@dataclass(frozen=True)
class EcosystemCiFullSettings:
    """The complete mode of the ecosystem-ci plugin: the heavy tests every repository declares, with hard limits."""

    enabled: bool = False
    per_repo_timeout_seconds: int = 1800
    total_timeout_seconds: int = 7200
    max_output_bytes: int = 1_000_000
    min_free_gb: float = 10.0
    allow_network: bool = False
    include_ci_validate: bool = True
    pass_env: tuple[str, ...] = ()
    tail_lines: int = 15
    approval_max_age_minutes: int = 30
    manifest_file: str = "hydra-umc.project.json"

    @property
    def min_free_bytes(self) -> int:
        return int(self.min_free_gb * GIB)


@dataclass(frozen=True)
class Settings:
    data_dir: str = "developer-node-data"
    language: str = "en"
    ingest: IngestSettings = field(default_factory=IngestSettings)
    repro: ReproSettings = field(default_factory=ReproSettings)
    checkouts: CheckoutSettings = field(default_factory=CheckoutSettings)
    panel: PanelSettings = field(default_factory=PanelSettings)
    server_push: ServerPushSettings = field(default_factory=ServerPushSettings)
    ecosystem_ci: EcosystemCiSettings = field(default_factory=EcosystemCiSettings)
    ecosystem_ci_full: EcosystemCiFullSettings = field(default_factory=EcosystemCiFullSettings)

    def data_path(self) -> Path:
        return Path(self.data_dir).expanduser()

    def switches(self) -> dict[str, bool]:
        return {
            "ingest": self.ingest.enabled,
            "repro": self.repro.enabled,
            "checkouts": self.checkouts.enabled,
            "panel": self.panel.enabled,
            "serverPush": self.server_push.enabled,
            "ecosystemCi": self.ecosystem_ci.enabled,
            "ecosystemCiFull": self.ecosystem_ci_full.enabled,
        }


# json key -> (attribute, kind); kinds: bool, int, float, str, strs
_SECTIONS: dict[str, dict[str, tuple[str, str]]] = {
    "ingest": {
        "enabled": ("enabled", "bool"),
        "maxBundleBytes": ("max_bundle_bytes", "int"),
        "requireTransportMac": ("require_transport_mac", "bool"),
        "secretEnv": ("secret_env", "str"),
        "secretFile": ("secret_file", "str"),
        "expectedToNode": ("expected_to_node", "str"),
        "maxClockSkewSeconds": ("max_clock_skew_seconds", "int"),
        "nonceRetentionSeconds": ("nonce_retention_seconds", "int"),
    },
    "repro": {
        "enabled": ("enabled", "bool"),
        "approvalMaxAgeMinutes": ("approval_max_age_minutes", "int"),
        "stepTimeoutSeconds": ("step_timeout_seconds", "int"),
        "maxSteps": ("max_steps", "int"),
        "maxOutputBytes": ("max_output_bytes", "int"),
        "allowedCommands": ("allowed_commands", "strs"),
    },
    "checkouts": {
        "enabled": ("enabled", "bool"),
        "mirrorsDir": ("mirrors_dir", "str"),
        "worktreesDir": ("worktrees_dir", "str"),
        "maxCacheGb": ("max_cache_gb", "float"),
        "allowedRemotes": ("allowed_remotes", "strs"),
        "gitTimeoutSeconds": ("git_timeout_seconds", "int"),
    },
    "panel": {
        "enabled": ("enabled", "bool"),
        "maxJournalEntries": ("max_journal_entries", "int"),
    },
    "serverPush": {
        "enabled": ("enabled", "bool"),
        "url": ("url", "str"),
        "nodeId": ("node_id", "str"),
        "tokenEnv": ("token_env", "str"),
        "tokenFile": ("token_file", "str"),
        "timeoutSeconds": ("timeout_seconds", "int"),
    },
    "ecosystemCi": {
        "enabled": ("enabled", "bool"),
        "workspace": ("workspace", "str"),
        "repos": ("repos", "strs"),
        "timeoutSeconds": ("timeout_seconds", "int"),
        "tailLines": ("tail_lines", "int"),
        "approvalMaxAgeMinutes": ("approval_max_age_minutes", "int"),
    },
    "ecosystemCiFull": {
        "enabled": ("enabled", "bool"),
        "perRepoTimeoutSeconds": ("per_repo_timeout_seconds", "int"),
        "totalTimeoutSeconds": ("total_timeout_seconds", "int"),
        "maxOutputBytes": ("max_output_bytes", "int"),
        "minFreeGb": ("min_free_gb", "float"),
        "allowNetwork": ("allow_network", "bool"),
        "includeCiValidate": ("include_ci_validate", "bool"),
        "passEnv": ("pass_env", "strs"),
        "tailLines": ("tail_lines", "int"),
        "approvalMaxAgeMinutes": ("approval_max_age_minutes", "int"),
        "manifestFile": ("manifest_file", "str"),
    },
}
_POSITIVE = {"max_bundle_bytes", "approval_max_age_minutes", "step_timeout_seconds", "max_steps", "max_output_bytes",
             "git_timeout_seconds", "max_journal_entries", "timeout_seconds", "tail_lines", "max_clock_skew_seconds",
             "nonce_retention_seconds", "per_repo_timeout_seconds", "total_timeout_seconds"}


def _convert(section: str, key: str, kind: str, value: Any) -> Any:
    where = f"{section}.{key}"
    if kind == "bool":
        if not isinstance(value, bool):
            raise SettingsError(f"{where} must be true or false (a real boolean)")
        return value
    if kind == "int":
        if isinstance(value, bool) or not isinstance(value, int):
            raise SettingsError(f"{where} must be a whole number")
        return value
    if kind == "float":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise SettingsError(f"{where} must be a number")
        return float(value)
    if kind == "str":
        if not isinstance(value, str):
            raise SettingsError(f"{where} must be text")
        return value
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise SettingsError(f"{where} must be a list of non-empty texts")
    return tuple(value)


def _section(name: str, raw: Any, cls: type) -> Any:
    if not isinstance(raw, dict):
        raise SettingsError(f"{name} must be an object")
    table = _SECTIONS[name]
    values: dict[str, Any] = {}
    for key, value in raw.items():
        if key not in table:
            raise SettingsError(f"{name}.{key} is not a setting of this node")
        attribute, kind = table[key]
        converted = _convert(name, key, kind, value)
        if attribute in _POSITIVE and converted < 1:
            raise SettingsError(f"{name}.{key} must be at least 1")
        if attribute in ("max_cache_gb", "min_free_gb") and converted <= 0:
            raise SettingsError(f"{name}.{key} must be greater than 0")
        values[attribute] = converted
    return cls(**values)


def parse_settings(raw: Any) -> Settings:
    if not isinstance(raw, dict):
        raise SettingsError("the configuration must be a JSON object")
    known = {"dataDir", "language", *_SECTIONS}
    for key in raw:
        if key not in known:
            raise SettingsError(f"{key} is not a setting of this node")
    language = raw.get("language", "en")
    if language not in LANGUAGES:
        raise SettingsError(f"language must be one of {', '.join(LANGUAGES)}")
    data_dir = raw.get("dataDir", Settings.data_dir)
    if not isinstance(data_dir, str) or not data_dir:
        raise SettingsError("dataDir must be a non-empty text")
    classes = {"ingest": IngestSettings, "repro": ReproSettings, "checkouts": CheckoutSettings, "panel": PanelSettings,
               "serverPush": ServerPushSettings, "ecosystemCi": EcosystemCiSettings, "ecosystemCiFull": EcosystemCiFullSettings}
    sections = {name: _section(name, raw[name], cls) for name, cls in classes.items() if name in raw}
    return Settings(
        data_dir=data_dir,
        language=language,
        ingest=sections.get("ingest", IngestSettings()),
        repro=sections.get("repro", ReproSettings()),
        checkouts=sections.get("checkouts", CheckoutSettings()),
        panel=sections.get("panel", PanelSettings()),
        server_push=sections.get("serverPush", ServerPushSettings()),
        ecosystem_ci=sections.get("ecosystemCi", EcosystemCiSettings()),
        ecosystem_ci_full=sections.get("ecosystemCiFull", EcosystemCiFullSettings()),
    )


def load_settings(path: str | Path | None) -> Settings:
    """The settings of the file at `path`; no path means all defaults (everything closed)."""
    if path is None:
        return Settings()
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as error:
        raise SettingsError(f"cannot read the configuration file: {error.strerror or 'error'}") from error
    except ValueError as error:
        raise SettingsError("the configuration file is not valid JSON") from error
    return parse_settings(raw)
