"""Ejecución diaria del pipeline según config/config.yaml."""

import logging
import time

import schedule

from src.config import cargar_config
from src.pipeline import ejecutar_pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


if __name__ == "__main__":
    config = cargar_config()
    hora = config.get("scheduler", {}).get("hora", "18:00")
    try:
        schedule.every().day.at(hora).do(ejecutar_pipeline)
    except schedule.ScheduleValueError as error:
        raise SystemExit(f"Hora inválida en config.yaml: {hora!r}. Use HH:MM, por ejemplo 18:00.") from error
    logging.info("Scheduler activo. Ejecución diaria a las %s", hora)
    while True:
        schedule.run_pending()
        time.sleep(1)
