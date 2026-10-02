"""Transformación Silver del DataFrame logístico."""

import pandas as pd

from .common import transformar_base


def transformar_logistica(df_logistica: pd.DataFrame) -> pd.DataFrame:
    """Limpia logística sin inventar eventos ni columnas."""
    return transformar_base(df_logistica, "logística")
