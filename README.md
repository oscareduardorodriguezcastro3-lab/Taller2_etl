# Laboratorio práctico de ETL — Kaismart Solutions S.A.S.

Proyecto académico de integración de ventas y eventos logísticos con Python y arquitectura Medallion.

## Descripción

El pipeline extrae ventas desde MySQL y eventos logísticos desde Excel, conserva los datos originales en Bronze, realiza análisis y perfil de calidad, limpia los datos en Silver y genera un dataset Gold integrado por `pedido_id`.

## Fuentes reales

- MySQL, base `clientes`, tabla `ventas`: 5.000 registros y 17 variables.
- Excel `data/raw/kaismart_eventos_logisticos.xlsx`: 50.000 registros y 14 variables.
- Clave compartida: `pedido_id`.

## Arquitectura

```text
MySQL --------\
               -> Bronze -> EDA/Calidad -> Silver -> Gold
Excel --------/
```

- RAW: archivo Excel y fuente MySQL original.
- Bronze: copias Parquet sin transformación.
- Silver: nombres, textos, fechas y numéricos estandarizados; se eliminan duplicados completos.
- Gold: logística integrada con ventas por `pedido_id`.

## Estructura actual

```text
config/config.yaml
data/raw data/bronze data/silver data/gold
logs/
notebooks/
outputs/eda outputs/quality outputs/business outputs/audit
src/
├── analysis/{business.py, eda.py, quality.py}
├── extract/{extract_mysql.py, extract_excel.py}
├── transform/{common.py, transform_ventas.py, transform_logistica.py}
├── load/{load_bronze.py, load_silver.py, load_gold.py, parquet.py}
├── config.py
└── pipeline.py
tests/
main.py scheduler.py requirements.txt .env.example
```

## Instalación

```powershell
py -3.14 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Configuración

Copie `.env.example` como `.env` y agregue las credenciales de MySQL. Configure rutas, tabla, `pedido_id`, autores y horario en `config/config.yaml`. Nunca publique `.env`.

## Paso a paso de ejecución

1. Abra PowerShell y entre al proyecto:

   ```powershell
   cd "\TALLER 2"
   ```

2. Cree y active el entorno virtual:

   ```powershell
   py -3.14 -m venv .venv
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\.venv\Scripts\Activate.ps1
   ```

3. Instale las dependencias:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Cree el archivo de credenciales y edítelo:

   ```powershell
   Copy-Item .env.example .env
   notepad .env
   ```

   Complete `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD` y `MYSQL_DATABASE`.

5. Verifique que MySQL esté disponible y que exista la base `clientes` con la tabla `ventas`.

6. Coloque el Excel real en:

   ```text
   data/raw/kaismart_eventos_logisticos.xlsx
   ```

7. Ejecute las pruebas:

   ```powershell
   python -m pytest -v
   ```

8. Ejecute el pipeline completo:

   ```powershell
   python main.py
   ```

9. Revise los resultados en `data/bronze`, `data/silver`, `data/gold`, `outputs` y `logs/etl.log`.

10. Para automatizar la ejecución diaria, ajuste `scheduler.hora` en `config/config.yaml` y ejecute:

   ```powershell
   python scheduler.py
   ```

## Ejecución

```powershell
python main.py
```

El acceso MySQL debe estar disponible desde el equipo. El pipeline no sustituye una fuente no disponible con datos inventados.

## Resultado real observado

- Ventas: 5.000 Bronze → 5.000 Silver.
- Logística: 50.000 Bronze → 49.901 Silver.
- Duplicados completos eliminados en logística: 99.
- Gold: 49.901 filas.
- Correspondencia `pedido_id` observada en la ejecución local: 100%.

## EDA y calidad

El EDA se ejecuta sobre Bronze antes de transformar y genera nulos, porcentajes, cardinalidad, tipos, fechas, identificadores, duplicados y estadísticas descriptivas. Los reportes están en `outputs/eda/`. No se imputan nulos automáticamente: un nulo puede representar una condición válida del proceso, como una calificación o incidencia no informada.

## Preguntas de negocio

Se generan respuestas para ciudad, canal, categoría, valor neto por ciudad, calificación, estado logístico, ciudad destino, transportadora, incidencia y tiempo promedio por transportadora. El resultado tabular está en `outputs/business/preguntas_negocio.csv`.

## Gráficos y reportes

- Gráficos: `outputs/eda/graficos/`.
- Informe completo: `outputs/eda/EDA_FINAL.md`.
- Resumen ejecutivo: `outputs/eda/resumen_ejecutivo.md`.
- Auditoría: `outputs/audit/reporte_pipeline.csv` e `integracion_gold.csv`.
- Checklist: `outputs/CHECKLIST_TALLER.md`.
- Logs: `logs/etl.log`.

## Automatización

```powershell
python scheduler.py
```

La hora se toma de `scheduler.hora` en `config/config.yaml`. Para detener el proceso use `Ctrl+C`.

## Pruebas

```powershell
python -m pytest -v
```

Las pruebas validan imports, existencia del Excel, preservación de DataFrames y escritura de capas cuando `pyarrow` está instalado.

## Conclusión

El proceso documenta trazabilidad desde las fuentes hasta Gold. En la ejecución local registrada, Bronze conservó las 55.000 filas, Silver eliminó solamente 99 duplicados completos de logística y Gold produjo 49.901 filas con la cardinalidad observada.
