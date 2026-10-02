"""Análisis exploratorio reutilizable."""

from pathlib import Path
from typing import Any
import json
import os
import pandas as pd
_matplotlib_cache = Path(__file__).resolve().parents[2] / ".matplotlib-cache"
_matplotlib_cache.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_matplotlib_cache))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _fechas(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if "fecha" in str(c).lower() or "date" in str(c).lower()]


def analizar_dataframe(df: pd.DataFrame, nombre: str) -> dict[str, Any]:
    """Construye un resumen EDA sin modificar el DataFrame."""
    fechas = _fechas(df)
    rangos = {}
    for col in fechas:
        serie = pd.to_datetime(df[col], errors="coerce")
        rangos[col] = {"min": str(serie.min()), "max": str(serie.max())}
    identificadores = [c for c in df.columns if c.lower().endswith("_id") or c.lower() == "id"]
    categoricas = [c for c in df.columns if df[c].dtype == "object" or str(df[c].dtype).startswith("category")]
    return {
        "nombre": nombre, "filas": int(df.shape[0]), "columnas": int(df.shape[1]),
        "variables": df.columns.tolist(), "tipos": {c: str(t) for c, t in df.dtypes.items()},
        "no_nulos": df.notna().sum().astype(int).to_dict(), "identificadores_posibles": identificadores,
        "categoricas": categoricas, "numericas": df.select_dtypes(include="number").columns.tolist(),
        "fechas": fechas, "rangos_fechas": rangos,
        "interpretacion": "Cada fila representa una venta." if "venta" in nombre.lower() else "Cada fila representa un evento logístico asociado a un pedido.",
    }


def guardar_eda(resumenes: list[dict[str, Any]], ruta: str | Path) -> None:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(resumenes, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def _perfil_nulos(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "columna": df.columns,
        "tipo_dato": [str(t) for t in df.dtypes],
        "total_registros": len(df),
        "nulos": df.isna().sum().values,
        "porcentaje_nulos": (df.isna().mean().mul(100).round(4)).values,
    }).sort_values("porcentaje_nulos", ascending=False)


def _clasificar_cardinalidad(columna: str, unicos: int, total: int, tipo: str) -> str:
    porcentaje = unicos / total if total else 0
    nombre = columna.lower()
    if nombre.endswith("_id") or nombre in {"id", "numero_guia"}:
        return "identificador"
    if tipo.startswith(("int", "float")) and porcentaje >= 0.5:
        return "alta cardinalidad"
    if porcentaje >= 0.5:
        return "alta cardinalidad"
    if porcentaje >= 0.1:
        return "media cardinalidad"
    return "baja cardinalidad"


def _perfil_cardinalidad(df: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for columna in df.columns:
        unicos = int(df[columna].nunique(dropna=True))
        filas.append({
            "columna": columna,
            "valores_unicos": unicos,
            "porcentaje_cardinalidad": round(unicos / len(df) * 100, 4) if len(df) else 0,
            "clasificacion": _clasificar_cardinalidad(columna, unicos, len(df), str(df[columna].dtype)),
        })
    return pd.DataFrame(filas).sort_values("valores_unicos", ascending=False)


def _perfil_tipos(df_original: pd.DataFrame, df_silver: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for columna in df_original.columns:
        tipo_original = str(df_original[columna].dtype)
        tipo_silver = str(df_silver[columna].dtype) if columna in df_silver.columns else "no disponible"
        observacion = "sin cambio de tipo"
        if tipo_original != tipo_silver:
            observacion = "tipo convertido en Silver"
        nombre = columna.lower()
        if "fecha" in nombre or "date" in nombre:
            observacion = "variable de fecha; se convierte con errors=coerce"
        elif columna.endswith("_id") or nombre in {"id", "numero_guia"}:
            observacion = "identificador; se conserva como clave o texto estandarizado"
        elif any(p in nombre for p in ("precio", "valor", "costo", "cantidad", "tiempo", "calificacion")):
            observacion = "variable numérica"
        elif tipo_original in ("object", "string"):
            observacion = "variable categórica o textual"
        filas.append({"columna": columna, "tipo_original": tipo_original, "tipo_silver": tipo_silver, "observacion": observacion})
    return pd.DataFrame(filas)


def _interpretar_nulos(df: pd.DataFrame) -> str:
    """Genera una interpretación prudente, sin afirmar que todo nulo sea error."""
    lineas = [f"# Interpretación de nulos: {len(df):,} registros", "", "Los nulos se describen; no se imputan durante EDA.", ""]
    for columna, cantidad in df.isna().sum().sort_values(ascending=False).items():
        if cantidad == 0:
            continue
        nombre = str(columna).lower()
        if any(p in nombre for p in ("calificacion", "incidencia", "observacion", "transportadora", "numero_guia")):
            criterio = "posiblemente válido por el proceso: puede no existir valoración, incidencia o dato logístico aún informado"
        elif nombre.startswith("unnamed"):
            criterio = "problema potencial de calidad: parece una columna auxiliar de la fuente y requiere revisión"
        else:
            criterio = "problema potencial de completitud; debe validarse con el significado del negocio"
        lineas.append(f"- `{columna}`: {int(cantidad):,} nulos; {criterio}.")
    if len(lineas) == 3:
        lineas.append("- No se encontraron nulos.")
    return "\n".join(lineas) + "\n"


def generar_eda_detallado(df: pd.DataFrame, nombre: str, carpeta: str | Path, df_silver: pd.DataFrame | None = None) -> dict[str, Any]:
    """Guarda perfiles detallados de un DataFrame Bronze y devuelve sus hallazgos."""
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    resumen = analizar_dataframe(df, nombre)
    resumen["nulos"] = df.isna().sum().astype(int).to_dict()
    resumen["porcentaje_nulos"] = df.isna().mean().mul(100).round(4).to_dict()
    resumen["valores_unicos"] = df.nunique(dropna=True).astype(int).to_dict()
    resumen["duplicados_completos"] = int(df.duplicated().sum())
    resumen["duplicados_identificadores"] = {c: int(df[c].duplicated().sum()) for c in df.columns if c.lower().endswith("_id") or c.lower() == "id"}
    resumen["muestra_head"] = df.head().to_dict("records")
    resumen["muestra_sample"] = df.sample(min(5, len(df)), random_state=42).to_dict("records") if len(df) else []
    (carpeta / f"eda_{nombre}.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    _perfil_nulos(df).to_csv(carpeta / f"nulos_{nombre}.csv", index=False, encoding="utf-8-sig")
    (carpeta / f"interpretacion_nulos_{nombre}.md").write_text(_interpretar_nulos(df), encoding="utf-8")
    _perfil_cardinalidad(df).to_csv(carpeta / f"cardinalidad_{nombre}.csv", index=False, encoding="utf-8-sig")
    if df_silver is not None:
        _perfil_tipos(df, df_silver).to_csv(carpeta / f"tipos_{nombre}.csv", index=False, encoding="utf-8-sig")
    numericas = df.select_dtypes(include="number")
    numericas.describe().T.to_csv(carpeta / f"estadisticos_{nombre}.csv", encoding="utf-8-sig")
    return resumen


def generar_graficos(df_ventas: pd.DataFrame, df_logistica: pd.DataFrame, df_ventas_silver: pd.DataFrame, df_logistica_silver: pd.DataFrame, df_gold: pd.DataFrame, carpeta: str | Path) -> None:
    """Genera gráficos solamente para columnas existentes."""
    carpeta = Path(carpeta); carpeta.mkdir(parents=True, exist_ok=True)

    def barras(df: pd.DataFrame, columna: str, archivo: str, titulo: str, eje: str, top: int = 15) -> None:
        if columna not in df.columns:
            return
        serie = df[columna].value_counts(dropna=False).head(top)
        fig, ax = plt.subplots(figsize=(10, 5)); serie.plot.bar(ax=ax, color="#4472C4")
        ax.set_title(titulo); ax.set_xlabel(eje); ax.set_ylabel("Cantidad"); plt.xticks(rotation=45, ha="right"); fig.tight_layout(); fig.savefig(carpeta / archivo, dpi=150); plt.close(fig)

    def histograma(df: pd.DataFrame, columna: str, archivo: str, titulo: str, eje: str) -> None:
        if columna not in df.columns:
            return
        serie = pd.to_numeric(df[columna], errors="coerce").dropna()
        if serie.empty:
            return
        fig, ax = plt.subplots(figsize=(9, 5)); ax.hist(serie, bins=20, color="#70AD47", edgecolor="white")
        ax.set_title(titulo); ax.set_xlabel(eje); ax.set_ylabel("Frecuencia"); fig.tight_layout(); fig.savefig(carpeta / archivo, dpi=150); plt.close(fig)

    for col, archivo, titulo in (("ciudad", "ventas_por_ciudad.png", "Ventas por ciudad"), ("canal", "ventas_por_canal.png", "Ventas por canal"), ("categoria", "ventas_por_categoria.png", "Ventas por categoría")):
        barras(df_ventas, col, archivo, titulo, col)
    histograma(df_ventas, "valor_neto", "distribucion_valor_neto.png", "Distribución de valor neto", "Valor neto")
    barras(df_ventas[df_ventas["calificacion_cliente"].notna()] if "calificacion_cliente" in df_ventas.columns else df_ventas, "calificacion_cliente", "calificacion_cliente.png", "Calificación de clientes informados", "Calificación")
    for col, archivo, titulo in (("estado_evento", "eventos_por_estado.png", "Eventos por estado"), ("ciudad_destino", "eventos_por_ciudad.png", "Eventos por ciudad destino"), ("transportadora", "eventos_por_transportadora.png", "Eventos por transportadora"), ("incidencia", "incidencias.png", "Incidencias más frecuentes")):
        barras(df_logistica, col, archivo, titulo, col)
    histograma(df_logistica, "tiempo_etapa_horas", "distribucion_tiempo_etapa.png", "Distribución del tiempo de etapa", "Horas")

    fig, ax = plt.subplots(figsize=(9, 5)); etiquetas = ["Ventas Bronze", "Ventas Silver", "Logística Bronze", "Logística Silver", "Gold"]
    valores = [len(df_ventas), len(df_ventas_silver), len(df_logistica), len(df_logistica_silver), len(df_gold)]
    ax.bar(etiquetas, valores, color=["#A5A5A5", "#4472C4", "#A5A5A5", "#70AD47", "#FFC000"]); ax.set_title("Resumen del proceso Medallion"); ax.set_ylabel("Filas"); plt.xticks(rotation=35, ha="right"); fig.tight_layout(); fig.savefig(carpeta / "resumen_medallion.png", dpi=150); plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 5)); etiquetas = ["Ventas Bronze", "Ventas Silver", "Logística Bronze", "Logística Silver"]; valores = [len(df_ventas), len(df_ventas_silver), len(df_logistica), len(df_logistica_silver)]; ax.bar(etiquetas, valores, color="#5B9BD5"); ax.set_title("Comparación de duplicados y filas"); ax.set_ylabel("Filas"); plt.xticks(rotation=35, ha="right"); fig.tight_layout(); fig.savefig(carpeta / "calidad_duplicados.png", dpi=150); plt.close(fig)


def generar_reportes_academicos(df_ventas: pd.DataFrame, df_logistica: pd.DataFrame, df_ventas_silver: pd.DataFrame, df_logistica_silver: pd.DataFrame, df_gold: pd.DataFrame, carpeta: str | Path) -> None:
    """Escribe conclusiones derivadas de los DataFrames reales del pipeline."""
    carpeta = Path(carpeta); carpeta.mkdir(parents=True, exist_ok=True)

    def top(df: pd.DataFrame, col: str) -> str:
        if col not in df.columns or df.empty:
            return "No evaluable"
        valores = df[col].value_counts(dropna=False)
        return f"{valores.index[0]} ({int(valores.iloc[0])})"

    def suma_por(df: pd.DataFrame, grupo: str, valor: str) -> str:
        if not {grupo, valor}.issubset(df.columns):
            return "No evaluable"
        valores = df.groupby(grupo, dropna=False)[valor].sum().sort_values(ascending=False)
        return f"{valores.index[0]} ({valores.iloc[0]:,.2f})"

    ventas_hallazgos = [
        f"La ciudad con más ventas es {top(df_ventas, 'ciudad')}.",
        f"El canal más frecuente es {top(df_ventas, 'canal')}.",
        f"La categoría con más registros es {top(df_ventas, 'categoria')}.",
        f"La ciudad con mayor valor neto acumulado es {suma_por(df_ventas, 'ciudad', 'valor_neto')}.",
        f"La calificación más frecuente entre los registros informados es {top(df_ventas[df_ventas['calificacion_cliente'].notna()] if 'calificacion_cliente' in df_ventas.columns else df_ventas, 'calificacion_cliente')}.",
    ]
    log_hallazgos = [
        f"El estado logístico más frecuente es {top(df_logistica, 'estado_evento')}.",
        f"La ciudad destino con más eventos es {top(df_logistica, 'ciudad_destino')}.",
        f"La transportadora con más eventos es {top(df_logistica, 'transportadora')}.",
        f"La incidencia más frecuente es {top(df_logistica, 'incidencia')}.",
        f"El tiempo promedio de etapa es {df_logistica['tiempo_etapa_horas'].mean():,.2f} horas." if 'tiempo_etapa_horas' in df_logistica.columns else "El tiempo promedio de etapa no es evaluable.",
    ]
    duplicados_v = int(df_ventas.duplicated().sum()); duplicados_l = int(df_logistica.duplicated().sum())
    correspondencia = int(df_logistica_silver["pedido_id"].isin(df_ventas_silver["pedido_id"]).sum()) if "pedido_id" in df_logistica_silver.columns and "pedido_id" in df_ventas_silver.columns else 0
    total_log = len(df_logistica_silver)
    porcentaje = correspondencia / total_log * 100 if total_log else 0
    contenido = [
        "# Análisis Exploratorio de Datos", "", "## 1. Objetivo", "Analizar las fuentes Bronze, documentar calidad y preparar evidencia para Silver y Gold.",
        "", "## 2. Descripción de las fuentes", f"- Ventas: {len(df_ventas):,} registros y {df_ventas.shape[1]} columnas.", f"- Logística: {len(df_logistica):,} registros y {df_logistica.shape[1]} columnas.", "- Clave de integración observada: `pedido_id`.",
        "", "## 3. Dataset de ventas", f"- Duplicados completos en Bronze: {duplicados_v}.", f"- Filas Silver: {len(df_ventas_silver):,}.", "- Hallazgos:", *[f"  - {x}" for x in ventas_hallazgos],
        "", "## 4. Dataset logístico", f"- Duplicados completos en Bronze: {duplicados_l}.", f"- Filas Silver: {len(df_logistica_silver):,}.", "- Hallazgos:", *[f"  - {x}" for x in log_hallazgos],
        "", "## 5. Hallazgos de calidad", f"- Ventas: {len(df_ventas):,} a {len(df_ventas_silver):,} filas.", f"- Logística: {len(df_logistica):,} a {len(df_logistica_silver):,}; se eliminaron {len(df_logistica) - len(df_logistica_silver):,} duplicados exactos.", "- Un pedido repetido no se interpreta como duplicado completo; la cardinalidad se analiza separadamente.",
        "", "## 6. Transformaciones realizadas", "- Se conservaron los originales en Bronze.", "- Se normalizaron nombres, espacios, categorías, fechas y variables numéricas según las reglas del código.", "- Se eliminaron únicamente filas completamente duplicadas; no se imputaron nulos automáticamente.",
        "", "## 7. Comparación Bronze vs Silver", f"- Ventas: {len(df_ventas):,} -> {len(df_ventas_silver):,}.", f"- Logística: {len(df_logistica):,} -> {len(df_logistica_silver):,}.",
        "", "## 8. Integración Gold", f"- Filas Gold: {len(df_gold):,}.", f"- Correspondencia logística Silver-ventas: {correspondencia:,} de {total_log:,} ({porcentaje:.2f}%).",
        "", "## 9. Preguntas de negocio", "Las respuestas detalladas se encuentran en `outputs/business/preguntas_negocio.csv`.",
        "", "## 10. Conclusiones", "Los resultados anteriores fueron calculados sobre los DataFrames reales extraídos y no sobre datos generados.",
    ]
    (carpeta / "EDA_FINAL.md").write_text("\n".join(contenido) + "\n", encoding="utf-8")
    ejecutivo = ["# Resumen ejecutivo", "", f"Se analizaron {len(df_ventas):,} ventas y {len(df_logistica):,} eventos logísticos.", f"Silver conservó {len(df_ventas_silver):,} ventas y {len(df_logistica_silver):,} eventos; eliminó {duplicados_l:,} duplicados exactos de logística.", f"Gold contiene {len(df_gold):,} filas y la correspondencia calculada fue {porcentaje:.2f}%.", "", "## Principales conclusiones", *[f"- {x}" for x in ventas_hallazgos[:2] + log_hallazgos[:3]]]
    (carpeta / "resumen_ejecutivo.md").write_text("\n".join(ejecutivo) + "\n", encoding="utf-8")
