from pathlib import Path
import importlib.util

import pandas as pd
import pytest

from src.load.load_bronze import guardar_logistica_bronze, guardar_ventas_bronze
from src.load.load_gold import integrar_y_guardar_gold
from src.load.load_silver import guardar_logistica_silver, guardar_ventas_silver


@pytest.mark.skipif(importlib.util.find_spec("pyarrow") is None, reason="requiere pyarrow")
def test_crea_archivos_bronze_silver_gold(tmp_path: Path) -> None:
    ventas = pd.DataFrame({"pedido_id": ["1"], "valor_neto": [100]})
    logistica = pd.DataFrame({"pedido_id": ["1"], "estado_evento": ["ENTREGADO"]})
    bronze, silver, gold = tmp_path / "bronze", tmp_path / "silver", tmp_path / "gold"
    guardar_ventas_bronze(ventas, bronze)
    guardar_logistica_bronze(logistica, bronze)
    guardar_ventas_silver(ventas, silver)
    guardar_logistica_silver(logistica, silver)
    resultado, cardinalidad = integrar_y_guardar_gold(ventas, logistica, "pedido_id", gold)
    assert resultado.shape[0] == 1
    assert cardinalidad == "many_to_one"
    assert (bronze / "ventas_bronze.parquet").exists()
    assert (silver / "logistica_silver.parquet").exists()
    assert (gold / "ventas_logistica_gold.parquet").exists()
