from __future__ import annotations

import argparse
import copy
import re
from collections.abc import Mapping, MutableMapping
from pathlib import Path
from typing import Any

import yaml

_BRACKET_KEY = re.compile(r"\[['\"]([^'\"]+)['\"]\]")


def parse_target(target: str) -> list[str]:
    if not target.startswith("$"):
        raise ValueError(f"Unsupported overlay target: {target}")

    keys: list[str] = []
    index = 1
    while index < len(target):
        if target[index] == ".":
            index += 1
            end = index
            while end < len(target) and target[end] not in ".[":
                end += 1
            if end == index:
                raise ValueError(f"Empty target component: {target}")
            keys.append(target[index:end])
            index = end
            continue

        if target[index] == "[":
            match = _BRACKET_KEY.match(target, index)
            if match is None:
                raise ValueError(f"Unsupported bracket target: {target}")
            keys.append(match.group(1))
            index = match.end()
            continue

        raise ValueError(f"Unsupported overlay target syntax: {target}")

    return keys


def deep_merge(target: MutableMapping[str, Any], update: Mapping[str, Any]) -> None:
    for key, value in update.items():
        existing = target.get(key)
        if isinstance(existing, MutableMapping) and isinstance(value, Mapping):
            deep_merge(existing, value)
        else:
            target[key] = copy.deepcopy(value)


def resolve_mapping(document: MutableMapping[str, Any], keys: list[str]) -> MutableMapping[str, Any]:
    current: Any = document
    for key in keys:
        if not isinstance(current, MutableMapping) or key not in current:
            raise KeyError(f"Overlay target does not exist: {'/'.join(keys)}")
        current = current[key]

    if not isinstance(current, MutableMapping):
        raise TypeError(f"Overlay target is not a mapping: {'/'.join(keys)}")
    return current


def apply_overlay(
    document: MutableMapping[str, Any], overlay: Mapping[str, Any]
) -> MutableMapping[str, Any]:
    actions = overlay.get("actions")
    if not isinstance(actions, list):
        raise ValueError("Overlay must contain an actions list")

    result = copy.deepcopy(document)
    for action in actions:
        if not isinstance(action, Mapping):
            raise TypeError("Each overlay action must be a mapping")
        target = action.get("target")
        update = action.get("update")
        if not isinstance(target, str) or not isinstance(update, Mapping):
            raise ValueError("Overlay action requires string target and mapping update")

        node = resolve_mapping(result, parse_target(target))
        deep_merge(node, update)

    return result


def load_yaml(path: Path) -> MutableMapping[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, MutableMapping):
        raise TypeError(f"Expected YAML mapping in {path}")
    return loaded


def main() -> None:
    parser = argparse.ArgumentParser(description="Build consolidated TransportERP OpenAPI contract")
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--overlay", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    document = load_yaml(args.base)
    overlay = load_yaml(args.overlay)
    consolidated = apply_overlay(document, overlay)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        yaml.safe_dump(consolidated, sort_keys=False, allow_unicode=True, width=100),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
