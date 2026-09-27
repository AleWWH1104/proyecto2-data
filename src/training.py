"""Utilidades comunes para entrenar modelos de segmentación binaria.

El módulo trabaja únicamente con cargadores de entrenamiento y validación. El
conjunto de prueba queda fuera de esta API para evitar usarlo durante el ajuste.
"""

from __future__ import annotations

import gc
import random
from collections.abc import Iterable
from dataclasses import dataclass
from numbers import Integral
from pathlib import Path
from typing import Callable, Mapping

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from torch import Tensor, nn
from torch.optim import AdamW, Optimizer
from torch.utils.data import DataLoader


SEED = 42


def _validar_entero_positivo(nombre: str, valor: int) -> None:
    if isinstance(valor, bool) or not isinstance(valor, Integral) or valor < 1:
        raise ValueError(f"{nombre} debe ser un entero mayor o igual que 1.")


@dataclass(frozen=True)
class ResultadoEntrenamiento:
    """Resumen estable de una ejecución de entrenamiento."""

    historial: pd.DataFrame
    mejor_epoca: int
    mejor_val_dice: float
    detencion_temprana: bool
    ruta_checkpoint: Path


def fijar_semilla(seed: int = SEED) -> None:
    """Fija las fuentes de aleatoriedad usadas por Python, NumPy y PyTorch."""

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)
    if torch.backends.cudnn.is_available():
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True


def _mascaras_4d(mascaras: Tensor) -> Tensor:
    if mascaras.ndim == 3:
        mascaras = mascaras.unsqueeze(1)
    if mascaras.ndim != 4 or mascaras.shape[1] != 1:
        raise ValueError("Las máscaras deben tener forma (B, 1, H, W) o (B, H, W).")
    return mascaras.float()


def adaptar_logits(salida: object, mascaras: Tensor) -> Tensor:
    """Extrae logits de un tensor o de ``salida.logits`` y ajusta su tamaño.

    SegFormer devuelve un objeto con ``logits`` a menor resolución. Los modelos
    de segmentation-models-pytorch devuelven el tensor directamente.
    """

    logits = salida if isinstance(salida, Tensor) else getattr(salida, "logits", None)
    if not isinstance(logits, Tensor):
        raise TypeError("La salida debe ser un tensor o exponer un tensor en .logits.")
    if logits.ndim != 4 or logits.shape[1] != 1:
        raise ValueError("Los logits deben tener forma (B, 1, H, W).")

    mascaras = _mascaras_4d(mascaras)
    if logits.shape[0] != mascaras.shape[0]:
        raise ValueError("Logits y máscaras deben tener el mismo tamaño de lote.")
    if logits.shape[-2:] != mascaras.shape[-2:]:
        logits = F.interpolate(
            logits,
            size=mascaras.shape[-2:],
            mode="bilinear",
            align_corners=False,
        )
    return logits


def dice_suave(logits: Tensor, mascaras: Tensor, suavizado: float = 1.0) -> Tensor:
    """Calcula Dice diferenciable por imagen a partir de logits."""

    mascaras = _mascaras_4d(mascaras)
    probabilidades = torch.sigmoid(logits)
    dimensiones = tuple(range(1, probabilidades.ndim))
    interseccion = (probabilidades * mascaras).sum(dim=dimensiones)
    denominador = probabilidades.sum(dim=dimensiones) + mascaras.sum(dim=dimensiones)
    return ((2.0 * interseccion + suavizado) / (denominador + suavizado)).mean()


def dice_binario(logits: Tensor, mascaras: Tensor, umbral: float = 0.5) -> Tensor:
    """Calcula Dice por imagen después de binarizar probabilidades."""

    mascaras = _mascaras_4d(mascaras)
    predicciones = torch.sigmoid(logits) >= umbral
    objetivos = mascaras >= 0.5
    dimensiones = tuple(range(1, predicciones.ndim))
    interseccion = (predicciones & objetivos).sum(dim=dimensiones).float()
    denominador = (
        predicciones.sum(dim=dimensiones).float()
        + objetivos.sum(dim=dimensiones).float()
    )
    return torch.where(
        denominador > 0,
        2.0 * interseccion / denominador.clamp_min(1.0),
        torch.ones_like(denominador),
    ).mean()


class PerdidaBCEDice(nn.Module):
    """Combina BCE con logits y pérdida Dice sin binarizar predicciones."""

    def __init__(self, peso_bce: float = 0.5, suavizado: float = 1.0) -> None:
        super().__init__()
        if not 0.0 <= peso_bce <= 1.0:
            raise ValueError("peso_bce debe estar entre 0 y 1.")
        self.peso_bce = peso_bce
        self.suavizado = suavizado

    def forward(self, logits: Tensor, mascaras: Tensor) -> Tensor:
        mascaras = _mascaras_4d(mascaras)
        bce = F.binary_cross_entropy_with_logits(logits, mascaras)
        perdida_dice = 1.0 - dice_suave(logits, mascaras, self.suavizado)
        return self.peso_bce * bce + (1.0 - self.peso_bce) * perdida_dice


def _usar_amp(dispositivo: torch.device, amp: bool) -> bool:
    return bool(amp and dispositivo.type == "cuda" and torch.cuda.is_available())


def ejecutar_epoca(
    modelo: nn.Module,
    cargador: DataLoader,
    criterio: Callable[[Tensor, Tensor], Tensor],
    dispositivo: str | torch.device,
    optimizador: Optimizer | None = None,
    amp: bool = False,
    escalador: torch.amp.GradScaler | None = None,
    acumulacion_gradientes: int = 1,
) -> dict[str, float | int]:
    """Ejecuta una época y pondera las métricas por número de imágenes."""

    _validar_entero_positivo("acumulacion_gradientes", acumulacion_gradientes)

    dispositivo = torch.device(dispositivo)
    es_entrenamiento = optimizador is not None
    modelo.train(es_entrenamiento)
    amp_activo = _usar_amp(dispositivo, amp)
    escalador = escalador or torch.amp.GradScaler("cuda", enabled=amp_activo)
    perdida_total = 0.0
    dice_total = 0.0
    numero_imagenes = 0
    numero_lotes = len(cargador)

    if numero_lotes == 0:
        raise ValueError("El cargador no contiene imágenes.")
    if es_entrenamiento:
        optimizador.zero_grad(set_to_none=True)

    for indice_lote, lote in enumerate(cargador):
        if not isinstance(lote, Mapping) or "image" not in lote or "mask" not in lote:
            raise TypeError("Cada lote debe incluir las claves 'image' y 'mask'.")
        imagenes = lote["image"].to(dispositivo)
        mascaras = _mascaras_4d(lote["mask"].to(dispositivo))
        cantidad = int(imagenes.shape[0])

        with torch.set_grad_enabled(es_entrenamiento):
            with torch.autocast(
                device_type=dispositivo.type,
                dtype=torch.float16,
                enabled=amp_activo,
            ):
                logits = adaptar_logits(modelo(imagenes), mascaras)
                perdida = criterio(logits, mascaras)

            if es_entrenamiento:
                inicio_ventana = (indice_lote // acumulacion_gradientes) * acumulacion_gradientes
                lotes_ventana = min(
                    acumulacion_gradientes,
                    numero_lotes - inicio_ventana,
                )
                escalador.scale(perdida / lotes_ventana).backward()
                termina_ventana = (
                    (indice_lote + 1) % acumulacion_gradientes == 0
                    or indice_lote + 1 == numero_lotes
                )
                if termina_ventana:
                    escalador.step(optimizador)
                    escalador.update()
                    optimizador.zero_grad(set_to_none=True)

        perdida_total += float(perdida.detach()) * cantidad
        dice_total += float(dice_binario(logits.detach(), mascaras)) * cantidad
        numero_imagenes += cantidad

    return {
        "loss": perdida_total / numero_imagenes,
        "dice": dice_total / numero_imagenes,
        "n_imagenes": numero_imagenes,
    }


def _medir_modelo_cuda(
    modelo: nn.Module,
    resolucion: int,
    batch_size: int,
    learning_rate: float,
    weight_decay: float,
    criterio: Callable[[Tensor, Tensor], Tensor],
    amp: bool,
) -> dict[str, float]:
    """Ejecuta un paso real y devuelve los picos totales del asignador CUDA."""

    dispositivo = torch.device("cuda")
    optimizador = None
    imagenes = mascaras = logits = perdida = None
    try:
        torch.cuda.reset_peak_memory_stats(dispositivo)
        modelo.to(dispositivo).train()
        optimizador = AdamW(
            modelo.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay,
        )
        amp_activo = _usar_amp(dispositivo, amp)
        escalador = torch.amp.GradScaler("cuda", enabled=amp_activo)
        imagenes = torch.randn(batch_size, 3, resolucion, resolucion, device=dispositivo)
        mascaras = torch.randint(
            0,
            2,
            (batch_size, 1, resolucion, resolucion),
            device=dispositivo,
            dtype=torch.float32,
        )

        optimizador.zero_grad(set_to_none=True)
        with torch.autocast(
            device_type="cuda",
            dtype=torch.float16,
            enabled=amp_activo,
        ):
            logits = adaptar_logits(modelo(imagenes), mascaras)
            perdida = criterio(logits, mascaras)
        escalador.scale(perdida).backward()
        escalador.step(optimizador)
        escalador.update()
        torch.cuda.synchronize(dispositivo)

        mib = 1024**2
        return {
            "pico_asignado_mib": torch.cuda.max_memory_allocated(dispositivo) / mib,
            "pico_reservado_mib": torch.cuda.max_memory_reserved(dispositivo) / mib,
        }
    finally:
        if optimizador is not None:
            optimizador.zero_grad(set_to_none=True)
        del imagenes, mascaras, logits, perdida, optimizador
        try:
            modelo.to("cpu")
        except (RuntimeError, torch.cuda.OutOfMemoryError):
            pass


def ejecutar_preflight_cuda(
    nombres_modelos: Iterable[str],
    crear_modelo: Callable[[str], nn.Module],
    resolucion: int,
    batch_size: int = 1,
    learning_rate: float = 1e-4,
    weight_decay: float = 1e-2,
    criterio: Callable[[Tensor, Tensor], Tensor] | None = None,
    amp: bool = True,
    medidor: Callable[..., dict[str, float]] | None = None,
) -> pd.DataFrame:
    """Prueba cada modelo con un paso CUDA antes del entrenamiento completo.

    ``medidor`` permite probar la orquestación sin fingir una medición CUDA real.
    Cuando se omite, se exige CUDA y se ejecutan forward, pérdida, backward y un
    paso AdamW para materializar también el estado del optimizador.
    """

    _validar_entero_positivo("batch_size", batch_size)
    _validar_entero_positivo("resolucion", resolucion)
    if medidor is None and not torch.cuda.is_available():
        raise RuntimeError("El preflight requiere una GPU CUDA disponible.")

    criterio = criterio or PerdidaBCEDice()
    medir = medidor or _medir_modelo_cuda
    resultados = []

    for nombre in nombres_modelos:
        modelo = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        try:
            modelo = crear_modelo(nombre)
            memoria = medir(
                modelo=modelo,
                resolucion=resolucion,
                batch_size=batch_size,
                learning_rate=learning_rate,
                weight_decay=weight_decay,
                criterio=criterio,
                amp=amp,
            )
            resultados.append({"modelo": nombre, **memoria})
        except (torch.cuda.OutOfMemoryError, RuntimeError) as error:
            es_oom = isinstance(error, torch.cuda.OutOfMemoryError) or (
                "out of memory" in str(error).lower() and "cuda" in str(error).lower()
            )
            if not es_oom:
                raise
            raise RuntimeError(
                f"Preflight CUDA sin memoria para {nombre} con batch físico "
                f"{batch_size} y resolución {resolucion}. Cierre otros procesos de GPU "
                "o reduzca la resolución; no inicie el entrenamiento completo."
            ) from error
        finally:
            del modelo
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    return pd.DataFrame(
        resultados,
        columns=["modelo", "pico_asignado_mib", "pico_reservado_mib"],
    )


def _guardar_checkpoint(
    ruta: Path,
    modelo: nn.Module,
    epoca: int,
    val_dice: float,
) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_suffix(ruta.suffix + ".tmp")
    torch.save(
        {
            "formato": 1,
            "modelo": modelo.state_dict(),
            "epoca": epoca,
            "val_dice": val_dice,
        },
        temporal,
    )
    temporal.replace(ruta)


def cargar_checkpoint(
    ruta: str | Path,
    modelo: nn.Module,
    dispositivo: str | torch.device = "cpu",
    estricto: bool = True,
) -> dict[str, int | float]:
    """Carga solo tensores y metadatos simples mediante ``weights_only=True``."""

    checkpoint = torch.load(
        Path(ruta),
        map_location=torch.device(dispositivo),
        weights_only=True,
    )
    if not isinstance(checkpoint, dict) or checkpoint.get("formato") != 1:
        raise ValueError("El checkpoint no tiene un formato compatible.")
    estado = checkpoint.get("modelo")
    if not isinstance(estado, dict):
        raise ValueError("El checkpoint no contiene un estado de modelo válido.")
    modelo.load_state_dict(estado, strict=estricto)
    return {
        "epoca": int(checkpoint["epoca"]),
        "val_dice": float(checkpoint["val_dice"]),
    }


def entrenar_modelo(
    modelo: nn.Module,
    cargador_train: DataLoader,
    cargador_val: DataLoader,
    ruta_checkpoint: str | Path,
    epocas: int = 20,
    paciencia: int = 5,
    learning_rate: float = 1e-4,
    weight_decay: float = 1e-2,
    dispositivo: str | torch.device = "cpu",
    criterio: Callable[[Tensor, Tensor], Tensor] | None = None,
    amp: bool = False,
    seed: int = SEED,
    mejora_minima: float = 0.0,
    acumulacion_gradientes: int = 1,
) -> ResultadoEntrenamiento:
    """Entrena con AdamW, guarda el mejor Dice de validación y detiene temprano."""

    if epocas < 1:
        raise ValueError("epocas debe ser al menos 1.")
    if paciencia < 1:
        raise ValueError("paciencia debe ser al menos 1.")
    if not mejora_minima >= 0.0:
        raise ValueError("mejora_minima debe ser mayor o igual que 0.")
    _validar_entero_positivo("acumulacion_gradientes", acumulacion_gradientes)

    fijar_semilla(seed)
    dispositivo = torch.device(dispositivo)
    modelo.to(dispositivo)
    criterio = criterio or PerdidaBCEDice()
    optimizador = AdamW(
        modelo.parameters(),
        lr=learning_rate,
        weight_decay=weight_decay,
    )
    amp_activo = _usar_amp(dispositivo, amp)
    escalador = torch.amp.GradScaler("cuda", enabled=amp_activo)
    ruta_checkpoint = Path(ruta_checkpoint)
    historial: list[dict[str, float | int]] = []
    mejor_val_dice = -float("inf")
    mejor_epoca = 0
    epocas_sin_mejora = 0
    detencion_temprana = False

    for epoca in range(1, epocas + 1):
        metricas_train = ejecutar_epoca(
            modelo,
            cargador_train,
            criterio,
            dispositivo,
            optimizador=optimizador,
            amp=amp_activo,
            escalador=escalador,
            acumulacion_gradientes=acumulacion_gradientes,
        )
        metricas_val = ejecutar_epoca(
            modelo,
            cargador_val,
            criterio,
            dispositivo,
            amp=amp_activo,
        )
        historial.append(
            {
                "epoca": epoca,
                "train_loss": metricas_train["loss"],
                "train_dice": metricas_train["dice"],
                "val_loss": metricas_val["loss"],
                "val_dice": metricas_val["dice"],
            }
        )

        val_dice = float(metricas_val["dice"])
        if val_dice > mejor_val_dice + mejora_minima:
            mejor_val_dice = val_dice
            mejor_epoca = epoca
            epocas_sin_mejora = 0
            _guardar_checkpoint(ruta_checkpoint, modelo, epoca, val_dice)
        else:
            epocas_sin_mejora += 1
            if epocas_sin_mejora >= paciencia:
                detencion_temprana = True
                break

    columnas = ["epoca", "train_loss", "train_dice", "val_loss", "val_dice"]
    return ResultadoEntrenamiento(
        historial=pd.DataFrame(historial, columns=columnas),
        mejor_epoca=mejor_epoca,
        mejor_val_dice=mejor_val_dice,
        detencion_temprana=detencion_temprana,
        ruta_checkpoint=ruta_checkpoint,
    )
