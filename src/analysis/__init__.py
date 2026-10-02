"""EDA, perfil de calidad y preguntas de negocio."""

from .eda import analizar_dataframe, guardar_eda, generar_eda_detallado, generar_graficos, generar_reportes_academicos
from .quality import perfilar_calidad, guardar_perfiles
from .business import ejecutar_preguntas_negocio, generar_estadisticas, generar_preguntas_negocio

__all__ = ["analizar_dataframe", "guardar_eda", "generar_eda_detallado", "generar_graficos", "generar_reportes_academicos", "perfilar_calidad", "guardar_perfiles", "ejecutar_preguntas_negocio", "generar_estadisticas", "generar_preguntas_negocio"]
