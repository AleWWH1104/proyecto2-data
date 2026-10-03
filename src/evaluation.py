"""Evaluación de los modelos entrenados sobre el conjunto de prueba.

Las métricas usan la misma convención que `src.training.dice_binario` (umbral 0.5,
promedio por imagen, 1.0 cuando predicción y máscara están vacías), para que el
Dice de prueba sea comparable con el Dice de validación del entrenamiento.
"""

from __future__ import annotations

import time
from collections.abc import Mapping
from pathlib import Path

import pandas as pd
import torch
from torch import Tensor, nn
from torch.utils.data import DataLoader

from src.models import crear_modelo
from src.training import adaptar_logits, cargar_checkpoint


UMBRAL = 0.5
COLUMNAS_METRICAS = ["modelo", "id", "organ", "dice", "iou", "segundos", "dispositivo"]


def _binarizar(logits, mascaras, umbral):
    if not 0.0 < umbral < 1.0:
        raise ValueError("umbral debe estar entre 0 y 1 sin incluirlos.")
    return (torch.sigmoid(logits) >= umbral).flatten(1), (mascaras >= 0.5).flatten(1)


def dice_por_imagen(logits: Tensor, mascaras: Tensor, umbral: float = UMBRAL) -> Tensor:
    """Dice de cada imagen del lote, con forma (B,)."""
    predicciones, objetivos = _binarizar(logits, mascaras, umbral)
    interseccion = (predicciones & objetivos).sum(dim=1).float()
    denominador = predicciones.sum(dim=1).float() + objetivos.sum(dim=1).float()
    return torch.where(
        denominador > 0,
        2.0 * interseccion / denominador.clamp_min(1.0),
        torch.ones_like(denominador),
    )


def iou_por_imagen(logits: Tensor, mascaras: Tensor, umbral: float = UMBRAL) -> Tensor:
    """IoU de cada imagen del lote, con forma (B,)."""
    predicciones, objetivos = _binarizar(logits, mascaras, umbral)
    interseccion = (predicciones & objetivos).sum(dim=1).float()
    union = (predicciones | objetivos).sum(dim=1).float()
    return torch.where(union > 0, interseccion / union.clamp_min(1.0), torch.ones_like(union))


def cargar_modelo_entrenado(nombre, ruta_checkpoint, dispositivo="cpu"):
    """Reconstruye un modelo y le carga su checkpoint, sin descargar pesos."""
    dispositivo = torch.device(dispositivo)
    modelo = crear_modelo(nombre, pesos_preentrenados=False)
    info = cargar_checkpoint(ruta_checkpoint, modelo, dispositivo)
    modelo.to(dispositivo)
    modelo.eval()
    return modelo, info


def _describir_dispositivo(dispositivo):
    if dispositivo.type == "cuda" and torch.cuda.is_available():
        return torch.cuda.get_device_name(dispositivo)
    return dispositivo.type


@torch.no_grad()
def evaluar_modelo(nombre, modelo, cargador, dispositivo="cpu", umbral=UMBRAL):
    """Evalúa un modelo y devuelve una fila por imagen.

    `segundos` reparte el tiempo del forward entre las imágenes del lote, así que
    es un tiempo por imagen exacto solo con batch_size=1.
    """
    dispositivo = torch.device(dispositivo)
    etiqueta = _describir_dispositivo(dispositivo)
    es_cuda = dispositivo.type == "cuda"
    modelo.eval()
    filas = []

    for lote in cargador:
        imagenes = lote["image"].to(dispositivo)
        mascaras = lote["mask"].to(dispositivo)

        if es_cuda:
            torch.cuda.synchronize()
        inicio = time.perf_counter()
        salida = modelo(imagenes)
        if es_cuda:
            torch.cuda.synchronize()
        transcurrido = time.perf_counter() - inicio

        logits = adaptar_logits(salida, mascaras)
        dados = dice_por_imagen(logits, mascaras, umbral).cpu()
        ious = iou_por_imagen(logits, mascaras, umbral).cpu()

        for i in range(len(dados)):
            filas.append({
                "modelo": nombre,
                "id": int(lote["id"][i]),
                "organ": str(lote["organ"][i]),
                "dice": float(dados[i]),
                "iou": float(ious[i]),
                "segundos": transcurrido / len(dados),
                "dispositivo": etiqueta,
            })

    return pd.DataFrame(filas, columns=COLUMNAS_METRICAS)


def evaluar_modelos(checkpoints: Mapping[str, str | Path], cargador, dispositivo="cpu", umbral=UMBRAL):
    """Evalúa varios modelos sobre el mismo cargador, uno a la vez en memoria."""
    partes = []
    for nombre, ruta in checkpoints.items():
        modelo, _ = cargar_modelo_entrenado(nombre, ruta, dispositivo)
        partes.append(evaluar_modelo(nombre, modelo, cargador, dispositivo, umbral))
        del modelo
        if torch.device(dispositivo).type == "cuda":
            torch.cuda.empty_cache()
    if not partes:
        return pd.DataFrame(columns=COLUMNAS_METRICAS)
    return pd.concat(partes, ignore_index=True)[COLUMNAS_METRICAS]


def resumen_por_modelo(metricas: pd.DataFrame) -> pd.DataFrame:
    """Dice, IoU y tiempo promedio por modelo, ordenado por Dice."""
    resumen = (
        metricas.groupby("modelo", sort=False)
        .agg(
            imagenes=("id", "count"),
            dice=("dice", "mean"),
            iou=("iou", "mean"),
            segundos_por_imagen=("segundos", "mean"),
        )
        .reset_index()
    )
    return resumen.sort_values("dice", ascending=False, ignore_index=True)


def resumen_por_organo(metricas: pd.DataFrame) -> pd.DataFrame:
    """Dice promedio por órgano y modelo, en formato ancho."""
    tabla = metricas.pivot_table(index="organ", columns="modelo", values="dice", aggfunc="mean")
    tabla.columns.name = None
    return tabla
