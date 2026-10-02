"""Extracción de ventas desde MySQL."""

import logging
import os
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def extraer_ventas(config: dict[str, Any] | None = None) -> pd.DataFrame:
    """Consulta la tabla configurada de la base ``clientes``."""
    if config is None:
        from ..config import cargar_config
        config = cargar_config()
    try:
        import mysql.connector
    except ImportError as error:
        raise RuntimeError("Instale mysql-connector-python con 'pip install -r requirements.txt'.") from error
    faltantes = [v for v in ("MYSQL_HOST", "MYSQL_USER", "MYSQL_PASSWORD") if not os.getenv(v)]
    if faltantes:
        raise RuntimeError(f"Faltan variables MySQL en .env: {', '.join(faltantes)}")
    conexion = None
    try:
        conexion = mysql.connector.connect(
            host=os.environ["MYSQL_HOST"],
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.environ["MYSQL_USER"],
            password=os.environ["MYSQL_PASSWORD"],
            database=os.getenv("MYSQL_DATABASE", "clientes"),
        )
        tabla = config["etl"].get("tabla_ventas", "ventas")
        if not tabla.replace("_", "").isalnum():
            raise ValueError("Nombre de tabla inválido en config.yaml")
        df_ventas = pd.read_sql(f"SELECT * FROM `{tabla}`", conexion)
        logger.info("MySQL: %s filas y %s columnas extraídas", *df_ventas.shape)
        return df_ventas
    except Exception:
        logger.exception("Error extrayendo ventas desde MySQL")
        raise
    finally:
        if conexion is not None:
            try:
                conexion.close()
            except Exception:
                logger.warning("No fue posible cerrar la conexión MySQL", exc_info=True)
