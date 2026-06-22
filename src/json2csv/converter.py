"""JSON to CSV converter module.

This module provides functionality to convert JSON files to CSV format,
handling nested structures, arrays, and robust exception management.
"""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class JsonToCsvError(Exception):
    """Base exception for JSON to CSV conversion errors."""


class InvalidJsonError(JsonToCsvError):
    """Raised when the input file contains invalid JSON."""


class EmptyDataError(JsonToCsvError):
    """Raised when the JSON data is empty or contains no records."""


class UnsupportedStructureError(JsonToCsvError):
    """Raised when the JSON structure cannot be flattened to CSV."""


def flatten_dict(data: dict[str, Any], parent_key: str = "", sep: str = ".") -> dict[str, Any]:
    """Flatten a nested dictionary into a single-level dictionary.

    Args:
        data: The dictionary to flatten.
        parent_key: The prefix to prepend to keys (used in recursion).
        sep: The separator between parent and child keys.

    Returns:
        A flattened dictionary with compound keys.

    Examples:
        >>> flatten_dict({"a": {"b": 1}})
        {'a.b': 1}
    """
    items: list[tuple[str, Any]] = []
    for key, value in data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, sep=sep).items())
        elif isinstance(value, list):
            items.append((new_key, json.dumps(value)))
        else:
            items.append((new_key, value))
    return dict(items)


def load_json(file_path: Path) -> Any:
    """Load and parse a JSON file.

    Args:
        file_path: Path to the JSON file.

    Returns:
        The parsed JSON data.

    Raises:
        FileNotFoundError: If the file does not exist.
        InvalidJsonError: If the file contains invalid JSON.
        PermissionError: If the file cannot be read due to permissions.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    logger.debug("Loading JSON from: %s", file_path)

    try:
        with file_path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        raise InvalidJsonError(f"Invalid JSON in '{file_path}': {exc}") from exc
    except UnicodeDecodeError as exc:
        raise InvalidJsonError(f"Encoding error reading '{file_path}': {exc}") from exc


def normalize_records(data: Any) -> list[dict[str, Any]]:
    """Normalize JSON data into a list of flat dictionaries.

    Handles:
    - A JSON array of objects.
    - A single JSON object (wrapped in a list).
    - A JSON object whose values are all objects (dict-of-dicts).

    Args:
        data: The parsed JSON data.

    Returns:
        A list of flat dictionaries ready for CSV writing.

    Raises:
        EmptyDataError: If the data contains no usable records.
        UnsupportedStructureError: If the structure cannot be normalized.
    """
    if data is None:
        raise EmptyDataError("JSON data is null.")

    if isinstance(data, list):
        if len(data) == 0:
            raise EmptyDataError("JSON array is empty.")
        records: list[dict[str, Any]] = []
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                raise UnsupportedStructureError(
                    f"Array element at index {i} is not an object (got {type(item).__name__})."
                )
            records.append(flatten_dict(item))
        return records

    if isinstance(data, dict):
        if len(data) == 0:
            raise EmptyDataError("JSON object is empty.")
        # Check if all values are dicts (dict-of-dicts pattern)
        if all(isinstance(v, dict) for v in data.values()):
            records = []
            for key, value in data.items():
                flat = flatten_dict(value)
                flat.setdefault("_key", key)
                records.append(flat)
            return records
        # Single object — wrap in list
        return [flatten_dict(data)]

    raise UnsupportedStructureError(
        f"Top-level JSON must be an array or object, got {type(data).__name__}."
    )


def write_csv(records: list[dict[str, Any]], output_path: Path, delimiter: str = ",") -> int:
    """Write a list of flat dictionaries to a CSV file.

    Args:
        records: The records to write.
        output_path: Destination path for the CSV file.
        delimiter: Column delimiter character (default: comma).

    Returns:
        The number of rows written (excluding the header).

    Raises:
        PermissionError: If the output file cannot be written.
        OSError: If any I/O error occurs during writing.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Collect all unique fieldnames preserving insertion order
    fieldnames: list[str] = []
    seen: set[str] = set()
    for record in records:
        for key in record:
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)

    logger.debug("Writing %d records to: %s", len(records), output_path)

    with output_path.open(mode="w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=fieldnames,
            delimiter=delimiter,
            extrasaction="ignore",
            restval="",
        )
        writer.writeheader()
        writer.writerows(records)

    return len(records)


def convert(
    input_path: str | Path,
    output_path: str | Path | None = None,
    delimiter: str = ",",
) -> Path:
    """Convert a JSON file to CSV format.

    This is the main public API of the module. It orchestrates loading,
    normalizing, and writing, with full exception handling at each stage.

    Args:
        input_path: Path to the source JSON file.
        output_path: Path for the output CSV file. If omitted, the output
            is placed alongside the input with a ``.csv`` extension.
        delimiter: Column delimiter for the CSV output (default: comma).

    Returns:
        The resolved path to the generated CSV file.

    Raises:
        FileNotFoundError: If the input file does not exist.
        InvalidJsonError: If the input contains malformed JSON.
        EmptyDataError: If the JSON data has no records to convert.
        UnsupportedStructureError: If the JSON structure cannot be mapped to CSV.
        PermissionError: If the output file cannot be written.
        ValueError: If ``input_path`` is not a file or ``delimiter`` is invalid.

    Example::

        output = convert("data.json")        # writes data.csv
        output = convert("data.json", "out.csv", delimiter=";")
    """
    if len(delimiter) != 1:
        raise ValueError(f"Delimiter must be a single character, got: {delimiter!r}")

    input_path = Path(input_path)
    if output_path is None:
        output_path = input_path.with_suffix(".csv")
    output_path = Path(output_path)

    logger.info("Converting '%s' → '%s'", input_path, output_path)

    data = load_json(input_path)
    records = normalize_records(data)
    rows_written = write_csv(records, output_path, delimiter=delimiter)

    logger.info("Done — %d row(s) written to '%s'.", rows_written, output_path)
    return output_path
