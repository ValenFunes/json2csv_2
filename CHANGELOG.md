# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] — 2025-01-01

### Added
- Initial implementation of `json2csv.converter` module.
- `flatten_dict()` — recursive flattening of nested dicts.
- `load_json()` — safe JSON loading with typed exceptions.
- `normalize_records()` — normalization of arrays, single objects, and dict-of-dicts.
- `write_csv()` — CSV writing with configurable delimiter and auto-created parent directories.
- `convert()` — high-level public API combining all steps.
- CLI entry point `json2csv` (via `json2csv.cli`).
- Custom exceptions: `JsonToCsvError`, `InvalidJsonError`, `EmptyDataError`, `UnsupportedStructureError`.
- Full unit-test suite with ≥ 85 % coverage.
- GitHub Actions CI workflow with ruff, black, mypy, pyright, bandit, pytest, and pdoc.
- MIT licence.
- CookieCutter-style project skeleton with `CONTEXT.md`, `README.md`, `CHANGELOG.md`, `VERSION`, `BUILD`.
