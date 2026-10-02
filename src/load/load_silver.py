"""Carga de DataFrames transformados Silver."""

from pathlib import Path
import pandas as pd

from .parquet import guardar_parquet


def guardar_ventas_silver(df: pd.DataFrame, carpeta: str | Path = "data/silver") -> None:
    guardar_parquet(df, Path(carpeta) / "ventas_silver.parquet")


def guardar_logistica_silver(df: pd.DataFrame, carpeta: str | Path = "data/silver") -> None:
    guardar_parquet(df, Path(carpeta) / "logistica_silver.parquet")
