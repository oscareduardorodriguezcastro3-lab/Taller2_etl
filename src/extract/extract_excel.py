"""Extracción de eventos logísticos desde Excel."""

import logging
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def extraer_logistica(config: dict[str, Any] | None = None) -> pd.DataFrame:
    """Lee el Excel logístico configurado y conserva sus columnas originales."""
    if config is None:
        from ..config import cargar_config
        config = cargar_config()
    ruta = Path(config["rutas"]["raw"]) / config["etl"].get("archivo_logistica", "kaismart_eventos_logisticos.xlsx")
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe el archivo logístico: {ruta}")
    try:
        df_logistica = pd.read_excel(ruta)
        logger.info("Excel: %s filas y %s columnas extraídas", *df_logistica.shape)
        return df_logistica
    except Exception:
        logger.exception("Error leyendo Excel logístico: %s", ruta)
        raise
