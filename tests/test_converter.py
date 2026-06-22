"""Unit tests for the json2csv converter.

Tests cover: happy paths, edge cases, and all exception conditions.
Target coverage: ≥ 85 %.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from json2csv.converter import (
    EmptyDataError,
    InvalidJsonError,
    JsonToCsvError,
    UnsupportedStructureError,
    convert,
    flatten_dict,
    load_json,
    normalize_records,
    write_csv,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def write_json(path: Path, data: object) -> None:
    """Write *data* as JSON to *path*."""
    path.write_text(json.dumps(data), encoding="utf-8")


# ---------------------------------------------------------------------------
# flatten_dict
# ---------------------------------------------------------------------------


class TestFlattenDict:
    """Tests for :func:`flatten_dict`."""

    def test_flat_dict_unchanged(self) -> None:
        """A already-flat dict is returned as-is."""
        assert flatten_dict({"a": 1, "b": 2}) == {"a": 1, "b": 2}

    def test_nested_one_level(self) -> None:
        """Single nesting level is flattened with dot separator."""
        assert flatten_dict({"a": {"b": 1}}) == {"a.b": 1}

    def test_nested_two_levels(self) -> None:
        """Two nesting levels produce compound keys."""
        result = flatten_dict({"a": {"b": {"c": 42}}})
        assert result == {"a.b.c": 42}

    def test_custom_separator(self) -> None:
        """Custom separator is used between key segments."""
        assert flatten_dict({"a": {"b": 1}}, sep="__") == {"a__b": 1}

    def test_list_value_serialised(self) -> None:
        """List values are JSON-serialised into a string."""
        result = flatten_dict({"items": [1, 2, 3]})
        assert result["items"] == "[1, 2, 3]"

    def test_empty_dict(self) -> None:
        """Empty dict returns empty dict."""
        assert flatten_dict({}) == {}

    def test_none_value(self) -> None:
        """None values are kept as-is."""
        assert flatten_dict({"x": None}) == {"x": None}

    def test_mixed_nested(self) -> None:
        """Mix of nested and flat keys are all handled."""
        data = {"a": 1, "b": {"c": 2, "d": {"e": 3}}}
        result = flatten_dict(data)
        assert result == {"a": 1, "b.c": 2, "b.d.e": 3}


# ---------------------------------------------------------------------------
# load_json
# ---------------------------------------------------------------------------


class TestLoadJson:
    """Tests for :func:`load_json`."""

    def test_loads_valid_json(self, tmp_path: Path) -> None:
        """Valid JSON file is loaded correctly."""
        p = tmp_path / "data.json"
        write_json(p, [{"a": 1}])
        assert load_json(p) == [{"a": 1}]

    def test_file_not_found(self, tmp_path: Path) -> None:
        """Missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_json(tmp_path / "missing.json")

    def test_invalid_json(self, tmp_path: Path) -> None:
        """Malformed JSON raises InvalidJsonError."""
        p = tmp_path / "bad.json"
        p.write_text("{not valid json}", encoding="utf-8")
        with pytest.raises(InvalidJsonError):
            load_json(p)

    def test_path_is_directory(self, tmp_path: Path) -> None:
        """Passing a directory raises ValueError."""
        with pytest.raises(ValueError, match="not a file"):
            load_json(tmp_path)

    def test_empty_json_file(self, tmp_path: Path) -> None:
        """Completely empty file raises InvalidJsonError."""
        p = tmp_path / "empty.json"
        p.write_text("", encoding="utf-8")
        with pytest.raises(InvalidJsonError):
            load_json(p)

    def test_unicode_content(self, tmp_path: Path) -> None:
        """Files with unicode characters are read correctly."""
        p = tmp_path / "uni.json"
        write_json(p, [{"name": "Ñoño", "ciudad": "Córdoba"}])
        result = load_json(p)
        assert result[0]["name"] == "Ñoño"


# ---------------------------------------------------------------------------
# normalize_records
# ---------------------------------------------------------------------------


class TestNormalizeRecords:
    """Tests for :func:`normalize_records`."""

    def test_array_of_objects(self) -> None:
        """Array of flat objects → list of flat dicts."""
        data = [{"a": 1}, {"a": 2}]
        result = normalize_records(data)
        assert result == [{"a": 1}, {"a": 2}]

    def test_single_object_wrapped(self) -> None:
        """Single top-level object is wrapped in a list."""
        result = normalize_records({"x": 10, "y": 20})
        assert result == [{"x": 10, "y": 20}]

    def test_dict_of_dicts(self) -> None:
        """Dict-of-dicts is expanded with _key column."""
        data = {"row1": {"v": 1}, "row2": {"v": 2}}
        result = normalize_records(data)
        keys = {r["_key"] for r in result}
        assert keys == {"row1", "row2"}

    def test_none_raises_empty(self) -> None:
        """None input raises EmptyDataError."""
        with pytest.raises(EmptyDataError):
            normalize_records(None)

    def test_empty_list_raises(self) -> None:
        """Empty list raises EmptyDataError."""
        with pytest.raises(EmptyDataError):
            normalize_records([])

    def test_empty_dict_raises(self) -> None:
        """Empty dict raises EmptyDataError."""
        with pytest.raises(EmptyDataError):
            normalize_records({})

    def test_array_with_non_dict_raises(self) -> None:
        """Array containing non-dict element raises UnsupportedStructureError."""
        with pytest.raises(UnsupportedStructureError):
            normalize_records([{"a": 1}, "not-a-dict"])

    def test_scalar_raises(self) -> None:
        """Top-level scalar raises UnsupportedStructureError."""
        with pytest.raises(UnsupportedStructureError):
            normalize_records(42)

    def test_nested_array_flattened(self) -> None:
        """Nested objects within array items are flattened."""
        data = [{"user": {"name": "Ana", "age": 30}}]
        result = normalize_records(data)
        assert result[0]["user.name"] == "Ana"
        assert result[0]["user.age"] == 30


# ---------------------------------------------------------------------------
# write_csv
# ---------------------------------------------------------------------------


class TestWriteCsv:
    """Tests for :func:`write_csv`."""

    def test_basic_write(self, tmp_path: Path) -> None:
        """Records are written with correct header and values."""
        records = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        out = tmp_path / "out.csv"
        count = write_csv(records, out)
        assert count == 2
        lines = out.read_text(encoding="utf-8").splitlines()
        assert lines[0] == "a,b"
        assert lines[1] == "1,2"

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        """Missing parent directories are created automatically."""
        out = tmp_path / "nested" / "dir" / "out.csv"
        write_csv([{"x": 1}], out)
        assert out.exists()

    def test_custom_delimiter(self, tmp_path: Path) -> None:
        """Custom delimiter is used in output."""
        out = tmp_path / "out.csv"
        write_csv([{"a": 1, "b": 2}], out, delimiter=";")
        lines = out.read_text(encoding="utf-8").splitlines()
        assert lines[0] == "a;b"

    def test_missing_fields_filled_empty(self, tmp_path: Path) -> None:
        """Records with missing keys get empty string for missing columns."""
        records = [{"a": 1, "b": 2}, {"a": 3}]
        out = tmp_path / "out.csv"
        write_csv(records, out)
        lines = out.read_text(encoding="utf-8").splitlines()
        assert lines[2] == "3,"

    def test_returns_row_count(self, tmp_path: Path) -> None:
        """Return value equals the number of records."""
        records = [{"v": i} for i in range(10)]
        out = tmp_path / "out.csv"
        assert write_csv(records, out) == 10


# ---------------------------------------------------------------------------
# convert  (integration)
# ---------------------------------------------------------------------------


class TestConvert:
    """Integration tests for :func:`convert`."""

    def test_simple_array(self, tmp_path: Path) -> None:
        """End-to-end conversion of a simple JSON array."""
        src = tmp_path / "data.json"
        write_json(src, [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}])
        out = convert(src)
        assert out.exists()
        lines = out.read_text(encoding="utf-8").splitlines()
        assert lines[0] == "name,age"
        assert "Alice" in lines[1]

    def test_default_output_path(self, tmp_path: Path) -> None:
        """Default output path uses same stem with .csv extension."""
        src = tmp_path / "mydata.json"
        write_json(src, [{"x": 1}])
        out = convert(src)
        assert out == tmp_path / "mydata.csv"

    def test_explicit_output_path(self, tmp_path: Path) -> None:
        """Explicit output path is honoured."""
        src = tmp_path / "in.json"
        dst = tmp_path / "custom.csv"
        write_json(src, [{"v": 42}])
        out = convert(src, dst)
        assert out == dst

    def test_nested_json(self, tmp_path: Path) -> None:
        """Nested JSON structures are flattened correctly."""
        src = tmp_path / "nested.json"
        write_json(src, [{"user": {"name": "Carlos", "score": 99}}])
        out = convert(src)
        header = out.read_text(encoding="utf-8").splitlines()[0]
        assert "user.name" in header

    def test_convert_returns_path(self, tmp_path: Path) -> None:
        """convert() returns a Path object."""
        src = tmp_path / "x.json"
        write_json(src, [{"k": "v"}])
        result = convert(src)
        assert isinstance(result, Path)

    def test_invalid_delimiter_raises(self, tmp_path: Path) -> None:
        """Multi-character delimiter raises ValueError."""
        src = tmp_path / "x.json"
        write_json(src, [{"k": "v"}])
        with pytest.raises(ValueError):
            convert(src, delimiter=";;")

    def test_file_not_found(self, tmp_path: Path) -> None:
        """Missing input raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            convert(tmp_path / "ghost.json")

    def test_invalid_json_raises(self, tmp_path: Path) -> None:
        """Malformed JSON raises InvalidJsonError."""
        src = tmp_path / "bad.json"
        src.write_text("oops", encoding="utf-8")
        with pytest.raises(InvalidJsonError):
            convert(src)

    def test_empty_array_raises(self, tmp_path: Path) -> None:
        """Empty JSON array raises EmptyDataError."""
        src = tmp_path / "empty.json"
        write_json(src, [])
        with pytest.raises(EmptyDataError):
            convert(src)

    def test_semicolon_delimiter(self, tmp_path: Path) -> None:
        """Semicolon delimiter produces correct CSV."""
        src = tmp_path / "d.json"
        write_json(src, [{"a": 1, "b": 2}])
        out = convert(src, delimiter=";")
        header = out.read_text(encoding="utf-8").splitlines()[0]
        assert "a;b" == header

    def test_string_input_path(self, tmp_path: Path) -> None:
        """String input path is accepted."""
        src = tmp_path / "s.json"
        write_json(src, [{"z": 9}])
        out = convert(str(src))
        assert out.exists()

    def test_single_object_json(self, tmp_path: Path) -> None:
        """Single JSON object (not array) is converted."""
        src = tmp_path / "single.json"
        write_json(src, {"name": "Test", "value": 1})
        out = convert(src)
        lines = out.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 2  # header + 1 row

    def test_exception_hierarchy(self) -> None:
        """All custom exceptions inherit from JsonToCsvError."""
        assert issubclass(InvalidJsonError, JsonToCsvError)
        assert issubclass(EmptyDataError, JsonToCsvError)
        assert issubclass(UnsupportedStructureError, JsonToCsvError)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


class TestCli:
    """Tests for the CLI entry point."""

    def test_cli_success(self, tmp_path: Path) -> None:
        """CLI exits 0 on success."""
        from json2csv.cli import main

        src = tmp_path / "data.json"
        write_json(src, [{"k": "v"}])
        rc = main([str(src)])
        assert rc == 0

    def test_cli_missing_file(self, tmp_path: Path) -> None:
        """CLI exits 1 when input file is missing."""
        from json2csv.cli import main

        rc = main([str(tmp_path / "nope.json")])
        assert rc == 1

    def test_cli_invalid_json(self, tmp_path: Path) -> None:
        """CLI exits 1 for invalid JSON."""
        from json2csv.cli import main

        src = tmp_path / "bad.json"
        src.write_text("!!!", encoding="utf-8")
        rc = main([str(src)])
        assert rc == 1

    def test_cli_explicit_output(self, tmp_path: Path) -> None:
        """CLI writes to explicit output path."""
        from json2csv.cli import main

        src = tmp_path / "in.json"
        dst = tmp_path / "out.csv"
        write_json(src, [{"a": 1}])
        rc = main([str(src), str(dst)])
        assert rc == 0
        assert dst.exists()

    def test_cli_verbose(self, tmp_path: Path) -> None:
        """CLI accepts --verbose flag without error."""
        from json2csv.cli import main

        src = tmp_path / "v.json"
        write_json(src, [{"x": 1}])
        rc = main([str(src), "--verbose"])
        assert rc == 0

    def test_cli_custom_delimiter(self, tmp_path: Path) -> None:
        """CLI accepts --delimiter flag."""
        from json2csv.cli import main

        src = tmp_path / "d.json"
        write_json(src, [{"a": 1, "b": 2}])
        rc = main([str(src), "--delimiter", ";"])
        assert rc == 0
