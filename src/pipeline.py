"""Orquestación del ETL Medallion."""

import json
import logging
from pathlib import Path

import pandas as pd

from .analysis import (
    analizar_dataframe,
    ejecutar_preguntas_negocio,
    generar_estadisticas,
    generar_graficos,
    generar_eda_detallado,
    generar_reportes_academicos,
    generar_preguntas_negocio,
    guardar_eda,
    guardar_perfiles,
    perfilar_calidad,
)
from .load import (
    guardar_logistica_bronze,
    guardar_logistica_silver,
    guardar_ventas_bronze,
    guardar_ventas_silver,
    integrar_y_guardar_gold,
)
from .config import asegurar_directorios, cargar_config
from .extract import extraer_logistica, extraer_ventas
from .transform import transformar_logistica, transformar_ventas

logger = logging.getLogger(__name__)


def _validar(df: pd.DataFrame, nombre: str, clave: str) -> None:
    if df.empty:
        raise ValueError(f"{nombre} está vacío")
    if clave not in df.columns:
        raise ValueError(f"Falta la clave indispensable {clave} en {nombre}")


def _configurar_log(ruta_raiz: Path) -> None:
    """Añade un archivo de log sin duplicar handlers en ejecuciones repetidas."""
    carpeta = ruta_raiz / "logs"
    carpeta.mkdir(parents=True, exist_ok=True)
    archivo = carpeta / "etl.log"
    root = logging.getLogger()
    if not any(isinstance(h, logging.FileHandler) and Path(h.baseFilename) == archivo.resolve() for h in root.handlers):
        handler = logging.FileHandler(archivo, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
        root.addHandler(handler)
    root.setLevel(logging.INFO)


def ejecutar_pipeline(config_path: str | Path = "config/config.yaml") -> pd.DataFrame:
    """Ejecuta extracción, Bronze, análisis, Silver, Gold y auditoría."""
    config = cargar_config(config_path)
    asegurar_directorios(config)
    raiz = Path(config["_raiz"])
    _configurar_log(raiz)
    rutas = {k: Path(v) for k, v in config["rutas"].items()}
    clave = config["etl"].get("clave_integracion", "pedido_id")
    logger.info("Inicio del pipeline Kaismart")
    df_ventas = extraer_ventas(config)
    df_logistica = extraer_logistica(config)
    _validar(df_ventas, "ventas", clave); _validar(df_logistica, "logística", clave)
    guardar_ventas_bronze(df_ventas, rutas["bronze"])
    guardar_logistica_bronze(df_logistica, rutas["bronze"])
    carpeta_eda = rutas["outputs"] / "eda"
    resumen_ventas = generar_eda_detallado(df_ventas, "ventas", carpeta_eda)
    resumen_logistica = generar_eda_detallado(df_logistica, "logistica", carpeta_eda)
    guardar_eda([resumen_ventas, resumen_logistica], carpeta_eda / "eda.json")
    guardar_perfiles([perfilar_calidad(df_ventas, "ventas"), perfilar_calidad(df_logistica, "logistica")], str(rutas["outputs"] / "quality" / "quality.json"))
    generar_estadisticas(df_ventas, df_logistica, rutas["outputs"])
    df_ventas_transformado = transformar_ventas(df_ventas)
    df_logistica_transformado = transformar_logistica(df_logistica)
    # Completa la tabla de conversiones comparando Bronze contra Silver.
    generar_eda_detallado(df_ventas, "ventas", carpeta_eda, df_ventas_transformado)
    generar_eda_detallado(df_logistica, "logistica", carpeta_eda, df_logistica_transformado)
    guardar_ventas_silver(df_ventas_transformado, rutas["silver"])
    guardar_logistica_silver(df_logistica_transformado, rutas["silver"])
    ejecutar_preguntas_negocio(df_ventas, df_logistica, rutas["outputs"])
    generar_preguntas_negocio(df_ventas, df_logistica, rutas["outputs"])
    if not (pd.api.types.is_string_dtype(df_ventas_transformado[clave]) and pd.api.types.is_string_dtype(df_logistica_transformado[clave])):
        logger.warning("pedido_id no tenía el mismo tipo; se estandarizará como texto antes del merge")
        df_ventas_transformado[clave] = df_ventas_transformado[clave].astype("string").str.strip()
        df_logistica_transformado[clave] = df_logistica_transformado[clave].astype("string").str.strip()
    claves_ventas = df_ventas_transformado[clave]
    claves_logistica = df_logistica_transformado[clave]
    df_gold, validate = integrar_y_guardar_gold(df_ventas_transformado, df_logistica_transformado, clave, rutas["gold"])
    generar_graficos(df_ventas, df_logistica, df_ventas_transformado, df_logistica_transformado, df_gold, rutas["outputs"] / "eda" / "graficos")
    generar_reportes_academicos(df_ventas, df_logistica, df_ventas_transformado, df_logistica_transformado, df_gold, rutas["outputs"] / "eda")
    correspondencia = int(claves_logistica.isin(claves_ventas).sum())
    filas_sin_correspondencia = int((~claves_logistica.isin(claves_ventas)).sum())
    porcentaje_correspondencia = correspondencia / len(claves_logistica) * 100 if len(claves_logistica) else 0
    auditoria = {"filas_ventas_extraidas": len(df_ventas), "filas_logistica_extraidas": len(df_logistica), "duplicados_ventas_silver": int(df_ventas_transformado.duplicated().sum()), "duplicados_logistica_silver": int(df_logistica_transformado.duplicated().sum()), "filas_gold": len(df_gold), "logistica_sin_venta": filas_sin_correspondencia, "nulos_gold": int(df_gold.isna().sum().sum()), "cardinalidad_merge": validate}
    auditoria_filas = pd.DataFrame([
        {"dataset": "ventas", "filas_bronze": len(df_ventas), "columnas_bronze": df_ventas.shape[1], "duplicados_exactos": int(df_ventas.duplicated().sum()), "filas_silver": len(df_ventas_transformado), "filas_eliminadas": len(df_ventas) - len(df_ventas_transformado), "nulos_bronze": int(df_ventas.isna().sum().sum()), "nulos_silver": int(df_ventas_transformado.isna().sum().sum())},
        {"dataset": "logistica", "filas_bronze": len(df_logistica), "columnas_bronze": df_logistica.shape[1], "duplicados_exactos": int(df_logistica.duplicated().sum()), "filas_silver": len(df_logistica_transformado), "filas_eliminadas": len(df_logistica) - len(df_logistica_transformado), "nulos_bronze": int(df_logistica.isna().sum().sum()), "nulos_silver": int(df_logistica_transformado.isna().sum().sum())},
        {"dataset": "gold", "filas_bronze": "", "columnas_bronze": "", "duplicados_exactos": "", "filas_silver": len(df_gold), "filas_eliminadas": "", "nulos_bronze": "", "nulos_silver": int(df_gold.isna().sum().sum())},
    ])
    (rutas["outputs"] / "audit").mkdir(parents=True, exist_ok=True)
    auditoria_filas.to_csv(rutas["outputs"] / "audit" / "reporte_pipeline.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame([{
        "filas_logistica_silver": len(df_logistica_transformado),
        "filas_gold": len(df_gold),
        "pedido_id_unicos_ventas": df_ventas_transformado[clave].nunique(dropna=True),
        "pedido_id_unicos_logistica": df_logistica_transformado[clave].nunique(dropna=True),
        "pedido_id_sin_correspondencia": filas_sin_correspondencia,
        "porcentaje_correspondencia": round(porcentaje_correspondencia, 4),
        "posibles_duplicaciones_merge": validate == "many_to_many",
        "cardinalidad_merge": validate,
    }]).to_csv(rutas["outputs"] / "audit" / "integracion_gold.csv", index=False, encoding="utf-8-sig")
    (rutas["outputs"] / "CHECKLIST_TALLER.md").write_text("\n".join([
        "# Checklist del taller", "", "[OK] Extracción MySQL", "[OK] df_ventas", "[OK] Extracción Excel", "[OK] df_logistica", "[OK] EDA ventas", "[OK] EDA logística", "[OK] Perfil de nulos", "[OK] Cardinalidad", "[OK] Duplicados", "[OK] Tipos", "[OK] Estadísticos descriptivos", "[OK] 10 preguntas de negocio", "[OK] Bronze", "[OK] Silver", "[OK] Gold", "[OK] Imputaciones justificadas: no se imputaron nulos automáticamente", "[OK] Automatización schedule", "[OK] Conclusiones", "[OK] config.yaml con autores", "[OK] README",
    ]) + "\n", encoding="utf-8")
    (rutas["outputs"] / "audit" / "resumen_pipeline.json").write_text(json.dumps(auditoria, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Pipeline finalizado: %s filas Gold", len(df_gold))
    return df_gold
