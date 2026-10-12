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
    # Preserve int64 parsing limits, but use Python integers for all arithmetic.
    tokens = np.asarray(str(fila["rle"]).split(), dtype=np.int64).tolist()
    dimensions = []
    for column in ("img_height", "img_width"):
        value = fila[column]
        dimension = int(value)
        if dimension <= 0 or value != dimension:
            raise ValueError("Dimensiones no enteras o inválidas")
        dimensions.append(dimension)
    area = dimensions[0] * dimensions[1]
    if len(tokens) % 2 or any(token <= 0 for token in tokens):
        raise ValueError("RLE inválido")
    previous_end = covered = 0
    for start, length in zip(tokens[::2], tokens[1::2]):
        if start > area or length > area - start + 1 or start <= previous_end:
            raise ValueError("RLE fuera de dimensiones o superpuesto")
        previous_end = start + length - 1
        covered += length
    return covered / area


def cargar_datos():
    """Load only CSV metadata; invalid assets stay empty, with explicit evidence."""
    issues = []
    specs = {
        "splits": (DATA / "splits.csv", ["id", "organ", "split"], {}, ["id"]),
        "train": (DATA / "train.csv", ["id", "organ"], {}, ["id"]),
        "metricas": (DATA / "metrics.csv", ["modelo", "id", "organ", "dice", "iou"],
                     {"dice": (0, 1), "iou": (0, 1), "segundos": (0, None)}, ["modelo", "id"]),
        "historial": (ARTEFACTOS / "historial_modelos.csv",
                      ["modelo", "epoca", "train_loss", "val_loss", "train_dice", "val_dice"],
                      {"epoca": (1, None), "train_loss": (0, None), "val_loss": (0, None),
                       "train_dice": (0, 1), "val_dice": (0, 1)}, ["modelo", "epoca"]),
        "experimentos": (ARTEFACTOS / "experimentos_modelos.csv", ["modelo", "mejor_epoca"],
                         {"mejor_epoca": (1, None), "mejor_val_dice": (0, 1),
                          "epocas_ejecutadas": (1, None)}, ["modelo"]),
    }
    result = {}
    for key, (path, required, bounds, unique) in specs.items():
        try:
            frame = pd.read_csv(path)
            if frame.empty or not set(required).issubset(frame.columns):
                raise ValueError("vacío o esquema incompleto")
            if frame[required].isna().any().any() or frame.duplicated(unique).any():
                raise ValueError("valores ausentes o filas duplicadas")
            for column in set(required) - set(bounds):
                if frame[column].astype(str).str.strip().eq("").any():
                    raise ValueError(f"{column}: valor vacío")
            for column, (low, high) in bounds.items():
                if column not in frame:
                    continue
                frame[column] = pd.to_numeric(frame[column], errors="raise")
                values = frame[column]
                if not np.isfinite(values).all() or (values < low).any() or (
                    high is not None and (values > high).any()
                ):
                    raise ValueError(f"{column}: fuera de rango")
            for column in ("epoca", "mejor_epoca"):
                if column in frame and (frame[column] % 1 != 0).any():
                    raise ValueError("época no entera")
            if "id" in frame:
                frame["id"] = frame["id"].astype(str)
            if "modelo" in frame and not frame["modelo"].isin(MODELOS).all():
                raise ValueError("modelo desconocido")
            if key == "splits" and not frame["split"].isin(["train", "val", "test"]).all():
                raise ValueError("split desconocido")
            result[key] = frame
        except (OSError, ValueError, UnicodeError, pd.errors.ParserError) as exc:
            result[key] = pd.DataFrame(columns=required)
            issues.append(f"{path.name}: no disponible o inválido ({exc}).")
    train = result["train"]
    if not train.empty:
        try:
            for column in ("age", "pixel_size", "img_height", "img_width"):
                if column in train:
                    train[column] = pd.to_numeric(train[column], errors="raise")
                    values = train[column].dropna()
                    minimum = 0 if column == "age" else np.nextafter(0., 1.)
                    if not np.isfinite(values).all() or (values < minimum).any():
                        raise ValueError(f"{column}: fuera de rango")
            if {"rle", "img_height", "img_width"}.issubset(train.columns):
                train["rle"] = train["rle"].fillna("")
                if train[["img_height", "img_width"]].isna().any().any():
                    raise ValueError("dimensiones ausentes")
                train["proporcion_ftu"] = train.apply(_proporcion_ftu, axis=1)
            splits = result["splits"]
            if not splits.empty:
                train = train.drop(columns=["split"], errors="ignore").merge(
                    splits[["id", "split"]], on="id", how="left", validate="one_to_one"
                )
            result["train"] = train
        except (ValueError, TypeError, OverflowError) as exc:
            result["train"] = pd.DataFrame(columns=["id", "organ"])
            issues.append(f"train.csv: metadatos inválidos ({exc}).")
    result["issues"] = issues
    return result


def performance_visible():
    """Keep the preference independent of page-specific widget lifetimes."""
    st.session_state.setdefault("performance_visible", True)
    st.session_state["_performance_visible"] = st.session_state["performance_visible"]

    def persist():
        st.session_state["performance_visible"] = st.session_state["_performance_visible"]

    return st.sidebar.toggle("Mostrar rendimiento", key="_performance_visible", on_change=persist)


def paired_metrics(frame, models):
    """Compare only identical image/organ sets, without recomputing predictions."""
    selected = frame[frame["modelo"].isin(models)]
    sets = [set(zip(group["id"], group["organ"])) for _, group in selected.groupby("modelo")]
    if len(sets) != len(models) or not sets:
        return selected.iloc[:0], len(selected)
    common = set.intersection(*sets)
    keep = [(identifier, organ) in common for identifier, organ in zip(selected["id"], selected["organ"])]
    paired = selected.loc[keep]
    return paired, len(selected) - len(paired)


@st.cache_resource
def cargar_modelo(nombre):
    """Carga un modelo entrenado en CPU una sola vez por sesión del servidor."""
    modelo, _ = cargar_modelo_entrenado(nombre, CHECKPOINTS / f"{nombre}.pt", "cpu")
    return modelo
