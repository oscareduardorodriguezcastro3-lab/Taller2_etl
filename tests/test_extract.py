"""Pruebas de extracción que no requieren conectarse a servicios reales."""

from pathlib import Path

import pytest

from src.extract.extract_excel import extraer_logistica


def test_excel_inexistente_lanza_error(tmp_path: Path) -> None:
    config = {"rutas": {"raw": str(tmp_path)}, "etl": {"archivo_logistica": "no_existe.xlsx"}}
    with pytest.raises(FileNotFoundError):
        extraer_logistica(config)
