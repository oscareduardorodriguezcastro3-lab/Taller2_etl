import pandas as pd

from src.transform.transform_logistica import transformar_logistica
from src.transform.transform_ventas import transformar_ventas


def test_transformaciones_no_modifican_originales() -> None:
    ventas = pd.DataFrame({"pedido_id": [1, 1], "Ciudad": [" Bogota ", " Bogota "]})
    logistica = pd.DataFrame({"pedido_id": [1], "estado_evento": [" En ruta "]})
    ventas_original = ventas.copy(deep=True)
    logistica_original = logistica.copy(deep=True)
    ventas_silver = transformar_ventas(ventas)
    logistica_silver = transformar_logistica(logistica)
    pd.testing.assert_frame_equal(ventas, ventas_original)
    pd.testing.assert_frame_equal(logistica, logistica_original)
    assert ventas_silver["pedido_id"].dtype.name == "string"
    assert logistica_silver.loc[0, "estado_evento"] == "EN RUTA"
