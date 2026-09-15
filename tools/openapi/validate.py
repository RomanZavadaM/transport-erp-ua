from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml
from openapi_spec_validator import validate_spec


def contains_value(value: Any, needle: str) -> bool:
    if isinstance(value, dict):
        return any(contains_value(item, needle) for item in value.values())
    if isinstance(value, list):
        return any(contains_value(item, needle) for item in value)
    return value == needle


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate TransportERP consolidated OpenAPI")
    parser.add_argument("contract", type=Path)
    args = parser.parse_args()

    spec = yaml.safe_load(args.contract.read_text(encoding="utf-8"))
    if not isinstance(spec, dict):
        raise TypeError("OpenAPI contract must be a mapping")

    validate_spec(spec)

    medical_result = spec["components"]["schemas"]["MedicalCheckCreate"]["properties"]["result"]
    assert medical_result["enum"] == ["FIT", "UNFIT"]
    assert not contains_value(spec, "FIT_WITH_RESTRICTIONS")

    paths = spec["paths"]
    assert "/releases/{release_id}/driver-predeparture-checks" in paths
    assert "/driver-predeparture-checks/{check_id}" in paths
    assert "/driver-predeparture-checks/{check_id}/invalidate" in paths

    waybill = spec["components"]["schemas"]["WaybillRead"]
    assert "document_role" in waybill["required"]
    assert "document_role" in waybill["properties"]

    create_waybill = paths["/duties/{duty_id}/waybills"]["post"]
    schema_ref = create_waybill["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    assert schema_ref == "#/components/schemas/WaybillCreate"

    print(f"Validated consolidated OpenAPI: {args.contract}")


if __name__ == "__main__":
    main()
