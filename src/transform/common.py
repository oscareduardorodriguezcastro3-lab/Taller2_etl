"""Reglas de limpieza compartidas y justificadas por el esquema observado."""

import logging
import re

import numpy as np
import pandas as pd
from pandas.api.types import is_object_dtype, is_string_dtype

logger = logging.getLogger(__name__)


def transformar_base(df: pd.DataFrame, nombre: str) -> pd.DataFrame:
    """Devuelve una copia limpia; nunca modifica el DataFrame de entrada."""
    salida = df.copy(deep=True)
    salida.columns = [re.sub(r"\s+", "_", str(c).strip().lower()) for c in salida.columns]
    for col in salida.columns:
        if is_object_dtype(salida[col]) or is_string_dtype(salida[col]):
            salida[col] = salida[col].map(lambda x: x.strip() if isinstance(x, str) else x)
            salida[col] = salida[col].replace(r"^\s*$", np.nan, regex=True)
            if any(p in col for p in ("ciudad", "canal", "categoria", "estado", "transport", "incidencia")):
                salida[col] = salida[col].str.upper()
    for col in salida.columns:
        if "fecha" in col or "date" in col:
            salida[col] = pd.to_datetime(salida[col], errors="coerce")
        elif any(p in col for p in ("cantidad", "precio", "valor", "costo", "tiempo", "calificacion")):
            salida[col] = pd.to_numeric(salida[col], errors="coerce")
    if "pedido_id" in salida.columns:
        salida["pedido_id"] = salida["pedido_id"].astype("string").str.strip()
    antes = len(salida)
    salida = salida.drop_duplicates().reset_index(drop=True)
    logger.info("Silver %s: %s filas originales, %s después de duplicados exactos", nombre, antes, len(salida))
    return salida
