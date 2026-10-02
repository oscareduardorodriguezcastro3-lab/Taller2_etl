"""Persistencia Parquet con diagnóstico amigable."""

from pathlib import Path
import pandas as pd


def guardar_parquet(df: pd.DataFrame, ruta: str | Path) -> None:
    try:
        Path(ruta).parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(ruta, index=False)
    except ImportError as error:
        raise RuntimeError("Instale pyarrow con 'pip install -r requirements.txt' para escribir Parquet.") from error
