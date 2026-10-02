"""Preguntas de negocio y estadísticas descriptivas exportables."""

from pathlib import Path
import logging
import pandas as pd
import json

logger = logging.getLogger(__name__)


def _guardar(df: pd.DataFrame, carpeta: Path, nombre: str) -> None:
    carpeta.mkdir(parents=True, exist_ok=True)
    df.to_csv(carpeta / f"{nombre}.csv", index=False, encoding="utf-8-sig")


def _conteo(df: pd.DataFrame, columna: str) -> pd.DataFrame:
    return df[columna].value_counts(dropna=False).rename_axis(columna).reset_index(name="cantidad")


def ejecutar_preguntas_negocio(ventas: pd.DataFrame, logistica: pd.DataFrame, outputs: str | Path) -> dict[str, str]:
    """Responde preguntas disponibles sin inventar columnas."""
    carpeta = Path(outputs) / "business"
    resultados: dict[str, str] = {}
    especificaciones = [
        (ventas, "ciudad", "ventas_por_ciudad"),
        (ventas, "canal", "ventas_por_canal"),
        (ventas, "categoria", "ventas_por_categoria"),
        (logistica, "estado_evento", "eventos_por_estado"),
        (logistica, "ciudad_destino", "eventos_por_ciudad_destino"),
        (logistica, "transportadora", "eventos_por_transportadora"),
        (logistica, "incidencia", "incidencias"),
    ]
    for df, col, nombre in especificaciones:
        if col in df.columns:
            _guardar(_conteo(df, col), carpeta, nombre)
            resultados[nombre] = "creado"
        else:
            logger.warning("Pregunta %s omitida: no existe la columna %s", nombre, col)
            resultados[nombre] = "omitido"
    if {"ciudad", "valor_neto"}.issubset(ventas.columns):
        _guardar(ventas.groupby("ciudad", dropna=False)["valor_neto"].sum().reset_index(name="valor_neto_total"), carpeta, "valor_neto_por_ciudad")
        resultados["valor_neto_por_ciudad"] = "creado"
    if "calificacion_cliente" in ventas.columns:
        _guardar(_conteo(ventas, "calificacion_cliente"), carpeta, "calificacion_cliente_frecuente")
        resultados["calificacion_cliente"] = "creado"
    if {"transportadora", "tiempo_etapa_horas"}.issubset(logistica.columns):
        _guardar(logistica.groupby("transportadora", dropna=False)["tiempo_etapa_horas"].mean().reset_index(name="promedio_horas"), carpeta, "tiempo_promedio_por_transportadora")
        resultados["tiempo_promedio_por_transportadora"] = "creado"
    return resultados


def generar_estadisticas(ventas: pd.DataFrame, logistica: pd.DataFrame, outputs: str | Path) -> None:
    carpeta = Path(outputs) / "statistics"
    carpeta.mkdir(parents=True, exist_ok=True)
    for df, nombre in ((ventas, "ventas"), (logistica, "logistica")):
        try:
            resumen = df.describe(include="all", datetime_is_numeric=True)
        except TypeError:
            resumen = df.describe(include="all")
        resumen.T.to_csv(carpeta / f"describe_{nombre}.csv", encoding="utf-8-sig")


def generar_preguntas_negocio(ventas: pd.DataFrame, logistica: pd.DataFrame, outputs: str | Path) -> pd.DataFrame:
    """Genera una fila por pregunta, con resultado e interpretación basada en columnas reales."""
    filas: list[dict[str, str]] = []

    def agregar(pregunta: str, resultado: object, interpretacion: str) -> None:
        filas.append({"pregunta": pregunta, "resultado": json.dumps(resultado, ensure_ascii=False, default=str), "interpretacion": interpretacion})

    def conteo(df: pd.DataFrame, col: str, pregunta: str) -> None:
        if col not in df.columns:
            logger.warning("No se puede responder: falta %s", col)
            agregar(pregunta, "NO EVALUABLE", f"No se encontró la columna {col}.")
            return
        tabla = df[col].value_counts(dropna=False)
        agregar(pregunta, tabla.head(10).to_dict(), f"Se muestran las categorías con mayor frecuencia de {col}.")

    conteo(ventas, "ciudad", "¿Qué ciudad registra mayor cantidad de ventas?")
    conteo(ventas, "canal", "¿Cómo se distribuyen las ventas por canal?")
    conteo(ventas, "categoria", "¿Qué categorías concentran mayor número de ventas?")
    if {"ciudad", "valor_neto"}.issubset(ventas.columns):
        tabla = ventas.groupby("ciudad", dropna=False)["valor_neto"].sum().sort_values(ascending=False).head(10)
        agregar("¿Qué ciudades generan mayor valor neto?", tabla.to_dict(), "Se ordenan las ciudades por suma de valor_neto.")
    else:
        agregar("¿Qué ciudades generan mayor valor neto?", "NO EVALUABLE", "Faltan ciudad o valor_neto.")
    conteo(ventas, "calificacion_cliente", "¿Cómo se distribuye la calificación del cliente?")
    conteo(logistica, "estado_evento", "¿Cuáles son los estados logísticos más frecuentes?")
    conteo(logistica, "ciudad_destino", "¿Qué ciudades destino concentran más eventos?")
    conteo(logistica, "transportadora", "¿Qué transportadoras procesan mayor número de eventos?")
    conteo(logistica, "incidencia", "¿Cuáles son las incidencias más frecuentes?")
    if {"transportadora", "tiempo_etapa_horas"}.issubset(logistica.columns):
        tabla = logistica.groupby("transportadora", dropna=False)["tiempo_etapa_horas"].mean().sort_values(ascending=False).head(10)
        agregar("¿Cuál es el tiempo promedio de etapa por transportadora?", tabla.to_dict(), "Se calcula la media de tiempo_etapa_horas por transportadora.")
    else:
        agregar("¿Cuál es el tiempo promedio de etapa por transportadora?", "NO EVALUABLE", "Faltan transportadora o tiempo_etapa_horas.")
    resultado = pd.DataFrame(filas)
    carpeta = Path(outputs) / "business"; carpeta.mkdir(parents=True, exist_ok=True)
    resultado.to_csv(carpeta / "preguntas_negocio.csv", index=False, encoding="utf-8-sig")
    return resultado
