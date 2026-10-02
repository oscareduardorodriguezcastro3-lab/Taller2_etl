"""Integración y persistencia Gold."""

from pathlib import Path
import pandas as pd

from .parquet import guardar_parquet


def integrar_y_guardar_gold(df_ventas: pd.DataFrame, df_logistica: pd.DataFrame, clave: str = "pedido_id", carpeta: str | Path = "data/gold") -> tuple[pd.DataFrame, str]:
    if clave not in df_ventas.columns or clave not in df_logistica.columns:
        raise ValueError(f"Falta {clave!r} en uno de los DataFrames")
    ventas = df_ventas.copy()
    logistica = df_logistica.copy()
    ventas[clave] = ventas[clave].astype("string").str.strip()
    logistica[clave] = logistica[clave].astype("string").str.strip()
    validacion = "many_to_one" if not ventas[clave].duplicated().any() else "many_to_many"
    gold = logistica.merge(ventas, on=clave, how="left", validate=validacion, suffixes=("_logistica", "_ventas"))
    carpeta = Path(carpeta)
    guardar_parquet(gold, carpeta / "ventas_logistica_gold.parquet")
    gold.head(1000).to_csv(carpeta / "ventas_logistica_gold_muestra.csv", index=False, encoding="utf-8-sig")
    return gold, validacion
