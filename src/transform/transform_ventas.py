"""Transformación Silver del DataFrame de ventas."""

import pandas as pd

from .common import transformar_base


def transformar_ventas(df_ventas: pd.DataFrame) -> pd.DataFrame:
    """Limpia ventas sin imputar nulos automáticamente."""
    return transformar_base(df_ventas, "ventas")
