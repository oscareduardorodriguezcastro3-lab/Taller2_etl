"""Carga y resolución de configuración del proyecto."""

from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


def cargar_config(ruta: str | Path = "config/config.yaml") -> dict[str, Any]:
    """Carga YAML y deja las rutas absolutas respecto a la raíz del proyecto."""
    ruta = Path(ruta)
    if not ruta.is_absolute():
        ruta = (Path(__file__).resolve().parents[1] / ruta).resolve()
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe el archivo de configuración: {ruta}")
    with ruta.open(encoding="utf-8") as archivo:
        config = yaml.safe_load(archivo) or {}
    raiz = ruta.parent.parent.resolve()
    config["_raiz"] = raiz
    config["rutas"] = {
        nombre: str((raiz / valor).resolve())
        for nombre, valor in config.get("rutas", {}).items()
    }
    faltantes = {"raw", "bronze", "silver", "gold", "outputs"} - set(config["rutas"])
    if faltantes:
        raise ValueError(f"Faltan rutas en config.yaml: {sorted(faltantes)}")
    load_dotenv(raiz / ".env")
    return config


def asegurar_directorios(config: dict[str, Any]) -> None:
    """Crea las carpetas de salida si no existen."""
    for ruta in config["rutas"].values():
        Path(ruta).mkdir(parents=True, exist_ok=True)
