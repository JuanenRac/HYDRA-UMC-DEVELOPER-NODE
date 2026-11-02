# =============================================================================
# HYDRA-UMC-DEVELOPER-NODE - src/hydra_umc_developer_node/schema.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""A small JSON Schema checker for the subset the contracts of this repository use.

The contracts in `contracts/` are normative JSON Schema files. This module checks a document against them without any dependency:
`type`, `required`, `properties`, `additionalProperties` (false or a schema), `items`, `enum`, `const`, `minLength`, `minItems` and
`minimum`. Anything else in a schema is ignored on purpose (annotations such as `description`), and an unknown `type` is an error so a
contract can never be silently skipped.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SchemaError(ValueError):
    """The document does not satisfy the contract; the message names the path and the reason."""


_TYPES: dict[str, tuple[type, ...]] = {
    "object": (dict,),
    "array": (list,),
    "string": (str,),
    "integer": (int,),
    "number": (int, float),
    "boolean": (bool,),
    "null": (type(None),),
}


def contracts_dir() -> Path:
    """The folder with the contract files: the repository checkout, or the copy that travels with the package."""
    here = Path(__file__).resolve()
    for candidate in (here.parents[2] / "contracts", here.parent / "contracts"):
        if candidate.is_dir():
            return candidate
    raise SchemaError("the contracts folder was not found")


def load_contract(name: str) -> dict[str, Any]:
    path = contracts_dir() / f"{name}.schema.json"
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise SchemaError(f"cannot read the contract {name}") from error
    if not isinstance(loaded, dict):
        raise SchemaError(f"the contract {name} is not an object")
    return loaded


def _type_ok(value: Any, expected: str) -> bool:
    if expected not in _TYPES:
        raise SchemaError(f"unknown type {expected!r} in a contract")
    if expected in ("integer", "number") and isinstance(value, bool):
        return False
    return isinstance(value, _TYPES[expected])


def _check(value: Any, schema: dict[str, Any], path: str) -> None:
    if "const" in schema and value != schema["const"]:
        raise SchemaError(f"{path}: must be {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise SchemaError(f"{path}: must be one of {schema['enum']!r}")
    expected = schema.get("type")
    if expected is not None:
        names = expected if isinstance(expected, list) else [expected]
        if not any(_type_ok(value, name) for name in names):
            raise SchemaError(f"{path}: must be of type {'/'.join(names)}")
    if isinstance(value, str) and len(value) < schema.get("minLength", 0):
        raise SchemaError(f"{path}: must not be empty")
    if isinstance(value, (int, float)) and not isinstance(value, bool) and "minimum" in schema and value < schema["minimum"]:
        raise SchemaError(f"{path}: must be at least {schema['minimum']}")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            raise SchemaError(f"{path}: needs at least {schema['minItems']} item(s)")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                _check(item, item_schema, f"{path}[{index}]")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                raise SchemaError(f"{path}: missing {key!r}")
        properties = schema.get("properties", {})
        extra = schema.get("additionalProperties", True)
        for key, item in value.items():
            if key in properties:
                _check(item, properties[key], f"{path}.{key}")
            elif extra is False:
                raise SchemaError(f"{path}: unknown key {key!r}")
            elif isinstance(extra, dict):
                _check(item, extra, f"{path}.{key}")


def validate(name: str, document: Any) -> None:
    """Raises `SchemaError` unless `document` satisfies the contract `name` (a file of `contracts/`)."""
    _check(document, load_contract(name), "$")
