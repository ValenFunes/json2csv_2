"""json2csv — Convert JSON files to CSV format.

Public API::

    from json2csv import convert
    output_path = convert("data.json")
"""

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

__all__ = [
    "convert",
    "flatten_dict",
    "load_json",
    "normalize_records",
    "write_csv",
    "JsonToCsvError",
    "InvalidJsonError",
    "EmptyDataError",
    "UnsupportedStructureError",
]

__version__ = "0.1.0"
