"""Datos, modelos y constantes compartidas por las páginas de la aplicación."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from informe.figuras_resultados import COLORES, MODELOS  # noqa: E402
from src import preprocess as pp  # noqa: E402
from src.evaluation import cargar_modelo_entrenado  # noqa: E402

DATA = RAIZ / "data"
ARTEFACTOS = DATA / "artefactos_entrenamiento"
CHECKPOINTS = ARTEFACTOS / "checkpoints"
CACHE_DIR = DATA / f"cache_{pp.IMG_SIZE}"

MODELO_SELECCIONADO = "segformer_mit_b0"
NOMBRES_COMPLETOS = {
    "unet_resnet34": "U-Net / ResNet34",
    "unetplusplus_resnet34": "U-Net++ / ResNet34",
    "segformer_mit_b0": "SegFormer / MIT-B0",
}
CIAN = "#00e5ff"

ARCHIVOS_DRIVE = {
    "train.csv": DATA / "train.csv",
    "cache_384/": CACHE_DIR,
    **{f"checkpoints/{m}.pt": CHECKPOINTS / f"{m}.pt" for m in MODELOS},
}


def archivos_faltantes():
    """Archivos del Drive que no están en data/."""
    return [nombre for nombre, ruta in ARCHIVOS_DRIVE.items() if not ruta.exists()]


def _proporcion_ftu(fila):
    pixeles = np.asarray(fila["rle"].split()[1::2], dtype=np.int64).sum()
    return pixeles / (fila["img_height"] * fila["img_width"])


@st.cache_data
def cargar_datos():
    """Devuelve un diccionario con los DataFrames del proyecto.

    `train` es None si falta train.csv; trae la columna `split` y `proporcion_ftu`.
    """
    splits = pd.read_csv(DATA / "splits.csv")
    train = None
    if (DATA / "train.csv").exists():
        train = pd.read_csv(DATA / "train.csv")
        train["proporcion_ftu"] = train.apply(_proporcion_ftu, axis=1)
        train = train.merge(splits[["id", "split"]], on="id")
    return {
        "train": train,
        "splits": splits,
        "metricas": pd.read_csv(DATA / "metrics.csv"),
        "historial": pd.read_csv(ARTEFACTOS / "historial_modelos.csv"),
        "experimentos": pd.read_csv(ARTEFACTOS / "experimentos_modelos.csv"),
    }


@st.cache_resource
def cargar_modelo(nombre):
    """Carga un modelo entrenado en CPU una sola vez por sesión del servidor."""
    modelo, _ = cargar_modelo_entrenado(nombre, CHECKPOINTS / f"{nombre}.pt", "cpu")
    return modelo
