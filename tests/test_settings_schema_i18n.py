import json
from pathlib import Path

import pytest
from hydra_umc_developer_node import i18n
from hydra_umc_developer_node.schema import SchemaError, validate
from hydra_umc_developer_node.settings import LANGUAGES, Settings, SettingsError, load_settings, parse_settings

ROOT = Path(__file__).resolve().parents[1]


def test_everything_is_closed_by_default() -> None:
    assert not any(Settings().switches().values())
    assert load_settings(None) == Settings()


def test_the_shipped_configuration_is_valid_and_closed() -> None:
    loaded = load_settings(ROOT / "configs" / "developer-node.json")
    assert loaded == Settings()


def test_a_switch_must_be_a_real_boolean() -> None:
    for bad in ("false", "true", 1, 0, None):
        with pytest.raises(SettingsError):
            parse_settings({"ingest": {"enabled": bad}})


def test_unknown_keys_and_bad_values_are_errors() -> None:
    for raw in ({"nope": 1}, {"ingest": {"nope": 1}}, {"language": "xx"}, {"repro": {"maxSteps": 0}}, {"repro": {"maxSteps": True}},
                {"checkouts": {"maxCacheGb": 0}}, {"checkouts": {"allowedRemotes": [""]}}, {"dataDir": ""}, [], {"panel": []}):
        with pytest.raises(SettingsError):
            parse_settings(raw)


def test_tuned_values_come_from_the_file(tmp_path: Path) -> None:
    path = tmp_path / "c.json"
    path.write_text(json.dumps({"checkouts": {"enabled": True, "maxCacheGb": 0.5, "allowedRemotes": ["/srv/x"]}, "language": "pt"}))
    loaded = load_settings(path)
    assert loaded.checkouts.enabled and loaded.checkouts.max_cache_bytes == 512 * 1024**2 and loaded.language == "pt"


def test_unreadable_or_invalid_files(tmp_path: Path) -> None:
    with pytest.raises(SettingsError):
        load_settings(tmp_path / "missing.json")
    bad = tmp_path / "bad.json"
    bad.write_text("{")
    with pytest.raises(SettingsError):
        load_settings(bad)


def test_schema_checks_types_required_and_extra_keys() -> None:
    good = {"schema_version": "1.0", "scenario_id": "s", "repro_case": "c", "steps": [{"argv": ["x"]}], "reproduced_when": {"exit_code_not": 0}}
    validate("repro_recipe", good)
    for broken in ({**good, "extra": 1}, {**good, "steps": []}, {**good, "schema_version": "2.0"},
                   {**good, "reproduced_when": {"exit_code_not": True}}, {**good, "steps": [{"argv": [""]}]}):
        with pytest.raises(SchemaError):
            validate("repro_recipe", broken)
    with pytest.raises(SchemaError):
        validate("repro_recipe", "text")


def test_every_message_has_the_eight_languages() -> None:
    assert LANGUAGES == ("en", "es", "de", "fr", "it", "ja", "zh", "pt")
    for key, row in i18n.MESSAGES.items():
        assert set(row) == set(LANGUAGES), key
        assert all(text.strip() for text in row.values()), key


def test_placeholders_match_in_every_language() -> None:
    import re

    for key, row in i18n.MESSAGES.items():
        fields = {lg: set(re.findall(r"\{(\w+)\}", text)) for lg, text in row.items()}
        assert len({frozenset(f) for f in fields.values()}) == 1, key


def test_european_portuguese_not_brazilian() -> None:
    joined = " ".join(row["pt"] for row in i18n.MESSAGES.values())
    for brazilian in ("arquivo", "usuário", "celular", "tela "):
        assert brazilian not in joined


def test_translation_lookup_and_fallback() -> None:
    assert i18n.t("msg.no_cases", "es") == "No hay casos."
    assert i18n.t("msg.no_cases", "xx") == "There are no cases."
    assert i18n.t("unknown.key") == "unknown.key"
    assert set(i18n.labels("ja")) == {key[6:] for key in i18n.MESSAGES if key.startswith("label.")}
