from functools import lru_cache
import pandas as pd
import logging
import os

# Configurar logger
logger = logging.getLogger("app")
logging.basicConfig(level=logging.INFO)

# Ruta al CSV
RUTA_CSV = "backend/datos/normalizado.csv"

_df_cache = None

def cargar_csv():
    global _df_cache
    if _df_cache is not None:
        return _df_cache

    try:
        if not os.path.exists(RUTA_CSV):
            raise FileNotFoundError(f"No se encontró el archivo: {RUTA_CSV}")

        # Leer CSV con separador ;
        df = pd.read_csv(RUTA_CSV, sep=";", encoding="utf-8", engine="python")

        # Convertir fechas
        columnas_fecha = [
            "fechahora_creacion", "fechahora_agendamiento", "fechahora_atencion",
            "fechahora_finalizacion", "fechahora_cerrado"
        ]
        for col in columnas_fecha:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        # Reemplazar valores nulos solo en columnas de texto
        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = df[col].fillna("")

        logger.info(f"Archivo CSV cargado correctamente con {df.shape[0]} filas.")
        _df_cache = df
        return _df_cache

    except Exception as e:
        logger.error(f"Error al cargar CSV: {e}")
        raise
