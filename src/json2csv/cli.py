"""Command-line interface for the json2csv converter.

Usage::

    python -m json2csv input.json [output.csv] [--delimiter CHAR]

Or, after installation::

    json2csv input.json [output.csv] [--delimiter CHAR]
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from json2csv.converter import (
    EmptyDataError,
    InvalidJsonError,
    JsonToCsvError,
    UnsupportedStructureError,
    convert,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser.

    Returns:
        Configured :class:`argparse.ArgumentParser` instance.
    """
    parser = argparse.ArgumentParser(
        prog="json2csv",
        description="Convert a JSON file to CSV format.",
    )
    parser.add_argument(
        "input",
        metavar="INPUT",
        type=Path,
        help="Path to the source JSON file.",
    )
    parser.add_argument(
        "output",
        metavar="OUTPUT",
        nargs="?",
        type=Path,
        default=None,
        help="Path for the output CSV file (default: same name as INPUT with .csv extension).",
    )
    parser.add_argument(
        "-d",
        "--delimiter",
        default=",",
        metavar="CHAR",
        help="Column delimiter character (default: comma).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG) logging.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the CLI.

    Args:
        argv: Argument list (defaults to :data:`sys.argv`).

    Returns:
        Exit code — ``0`` on success, ``1`` on error.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        output = convert(
            input_path=args.input,
            output_path=args.output,
            delimiter=args.delimiter,
        )
        print(f"✓ CSV written to: {output}")
        return 0
    except FileNotFoundError as exc:
        logger.error("File not found — %s", exc)
    except InvalidJsonError as exc:
        logger.error("Invalid JSON — %s", exc)
    except EmptyDataError as exc:
        logger.error("Empty data — %s", exc)
    except UnsupportedStructureError as exc:
        logger.error("Unsupported structure — %s", exc)
    except JsonToCsvError as exc:
        logger.error("Conversion error — %s", exc)
    except (PermissionError, OSError) as exc:
        logger.error("I/O error — %s", exc)
    except ValueError as exc:
        logger.error("Invalid argument — %s", exc)

    return 1


if __name__ == "__main__":
    sys.exit(main())
