"""Perfil de calidad sin modificar datos."""

from pathlib import Path
from typing import Any
import json
import pandas as pd


def perfilar_calidad(df: pd.DataFrame, nombre: str) -> dict[str, Any]:
    """Devuelve nulos, cardinalidad, duplicados y tipos sin transformar."""
    nulos = pd.DataFrame({"cantidad": df.isna().sum(), "porcentaje": df.isna().mean().mul(100)}).sort_values("porcentaje", ascending=False)
    cardinalidad = df.nunique(dropna=True).sort_values(ascending=False)
    ids = [c for c in df.columns if c.lower().endswith("_id") or c.lower() == "id"]
    return {
        "nombre": nombre,
        "nulos": nulos.reset_index().rename(columns={"index": "columna"}).to_dict("records"),
        "cardinalidad": cardinalidad.to_dict(),
        "alta_cardinalidad": cardinalidad[cardinalidad >= max(20, len(df) * 0.8)].index.tolist(),
        "baja_cardinalidad": cardinalidad[cardinalidad <= 20].index.tolist(),
        "duplicados_filas": int(df.duplicated().sum()),
        "duplicados_identificadores": {c: int(df[c].duplicated().sum()) for c in ids},
        "tipos": {c: str(t) for c, t in df.dtypes.items()},
    }


def guardar_perfiles(perfiles: list[dict[str, Any]], ruta: str | Path) -> None:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(perfiles, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
