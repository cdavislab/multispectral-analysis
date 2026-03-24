"""Shared helpers for schema-driven settings coercion and validation."""

from typing import Any


def coerce_value(rule: str | None, value: Any) -> Any:
    """Coerce a single value according to a coercion rule."""
    if rule is None:
        return value
    if rule == "int":
        return int(value) if str(value).strip() != "" else 0
    if rule == "float":
        return float(value) if str(value).strip() != "" else 0.0
    if rule == "float_or_none":
        return None if str(value).strip() == "" else float(value)
    if rule == "str_or_none":
        return None if str(value).strip() == "" else str(value)
    return value


def expected_value_description(rule: str | None) -> str:
    """Return a short human-readable expectation for a coercion rule."""
    if rule == "int":
        return "an integer"
    if rule == "float":
        return "a number"
    if rule == "float_or_none":
        return "a number or blank"
    if rule == "str_or_none":
        return "text or blank"
    return "a valid value"


def schema_label_map(schema: list[dict[str, Any]]) -> dict[str, str]:
    """Build a mapping from schema keys to user-facing labels."""
    labels: dict[str, str] = {}
    for item in schema:
        kind = item.get("kind")
        if kind in {"entry", "checkbutton"} and "key" in item:
            labels[item["key"]] = item.get("label", item["key"])
        elif kind == "double":
            for field in item.get("fields", []):
                key = field.get("key")
                if not key:
                    continue
                labels[key] = f"{item.get('label', key)} ({field.get('sublabel', key)})"
    return labels


def coerce_with_validation(
    settings: dict[str, Any],
    coerce_map: dict[str, str],
) -> tuple[dict[str, Any], list[tuple[str, Any, str | None]]]:
    """Coerce settings and collect invalid values without raising.

    Returns:
        Tuple of (coerced_settings, invalid_entries) where invalid entries are
        tuples of (key, raw_value, coercion_rule).
    """
    coerced: dict[str, Any] = {}
    invalid: list[tuple[str, Any, str | None]] = []

    for key, value in settings.items():
        rule = coerce_map.get(key)
        try:
            coerced[key] = coerce_value(rule, value)
        except (ValueError, TypeError):
            invalid.append((key, value, rule))

    return coerced, invalid


def format_invalid_values_message(
    schema: list[dict[str, Any]],
    invalid: list[tuple[str, Any, str | None]],
) -> str:
    """Format invalid entries as a multi-line user-facing error message."""
    labels = schema_label_map(schema)
    lines: list[str] = []
    for key, value, rule in invalid:
        label = labels.get(key, key)
        expected = expected_value_description(rule)
        lines.append(f"- {label}: {value!r} (expected {expected})")
    return "Please fix the following invalid value(s):\n\n" + "\n".join(lines)
