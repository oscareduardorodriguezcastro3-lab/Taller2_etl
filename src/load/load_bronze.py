"""Carga de las copias originales Bronze."""

from pathlib import Path
import pandas as pd

from .parquet import guardar_parquet


def guardar_ventas_bronze(df: pd.DataFrame, carpeta: str | Path = "data/bronze") -> None:
    guardar_parquet(df.copy(deep=True), Path(carpeta) / "ventas_bronze.parquet")


def guardar_logistica_bronze(df: pd.DataFrame, carpeta: str | Path = "data/bronze") -> None:
    guardar_parquet(df.copy(deep=True), Path(carpeta) / "logistica_bronze.parquet")
