"""Helpers that check requests against the backend's OpenAPI 3.0 contract."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from openapi_schema_validator import OAS30Validator

# The backend owns the contract: keep contracts/openapi.yaml in sync with its repository
# (or point OPENAPI_SPEC at a fresh copy in CI).
SPEC_PATH = Path(
    os.environ.get(
        "OPENAPI_SPEC",
        Path(__file__).parent.parent.parent.parent.parent
        / "contracts"
        / "openapi"
        / "bundled"
        / "openapi.yaml",
    )
)


def load_spec() -> dict[str, Any]:
    return yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))


def dereference(node: Any, spec: dict[str, Any]) -> Any:
    """Inline local `$ref`s (the contract has no recursive schemas)."""
    if isinstance(node, dict):
        if "$ref" in node:
            target: Any = spec
            for part in node["$ref"].removeprefix("#/").split("/"):
                target = target[part]
            return dereference(target, spec)
        return {key: dereference(value, spec) for key, value in node.items()}
    if isinstance(node, list):
        return [dereference(item, spec) for item in node]
    return node


def request_body_schema(spec: dict[str, Any], path: str, method: str) -> dict[str, Any]:
    operation = spec["paths"][path][method]
    schema = operation["requestBody"]["content"]["application/json"]["schema"]
    return dereference(schema, spec)


def schema_errors(schema: dict[str, Any], payload: Any) -> list[str]:
    errors = OAS30Validator(schema).iter_errors(payload)
    return sorted(
        f"{'.'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
        for e in errors
    )
