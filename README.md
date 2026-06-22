# json2csv

> Convert JSON files to CSV format with robust exception handling.

[![CI](https://github.com/ValenFunes/json2csv_2/actions/workflows/ci.yml/badge.svg)](https://github.com/ValenFunes/json2csv_2/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

## Overview

`json2csv` es una herramienta CLI y librería Python que convierte archivos JSON a formato CSV. Soporta:

- Arrays de objetos planos
- Objetos anidados — aplanados con notación punto (ej: `usuario.nombre`)
- Objeto JSON único — convertido en una sola fila
- Dict-of-dicts — cada clave se convierte en una fila con columna `_key`
- Valores de tipo lista — serializados como JSON string en la celda

## Instalación

```bash
git clone https://github.com/ValenFunes/json2csv_2.git
cd json2csv_2
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

## Uso

### CLI

```bash
json2csv input.json
json2csv input.json output.csv
json2csv input.json --delimiter ";"
json2csv input.json --verbose
```

### API Python

```python
from json2csv import convert
output = convert("data.json")
output = convert("data.json", "out.csv", delimiter=";")
```

## Excepciones

| Excepción | Cuándo se lanza |
|---|---|
| `FileNotFoundError` | El archivo de entrada no existe |
| `InvalidJsonError` | El JSON está malformado |
| `EmptyDataError` | El JSON es nulo o está vacío |
| `UnsupportedStructureError` | La estructura no puede mapearse a CSV |
| `PermissionError` | No se puede leer o escribir el archivo |

## Desarrollo

```bash
ruff check src/ tests/
black --check src/ tests/
mypy src/
pyright src/
bandit -r src/ -c pyproject.toml
pytest
```

## Documentación

Generada automáticamente con pdoc:

```bash
pdoc src/json2csv -o docs/
```

## Licencia

[MIT](LICENSE) © Valentina Funes