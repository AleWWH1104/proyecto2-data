"""Orquestador determinista del entrenamiento de Persona 2 en Windows nativo."""

from __future__ import annotations

import argparse
import gc
import json
import os
import platform
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping

import pandas as pd


RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

RESOLUCION = 384
BATCH_FISICO = 1
ACUMULACION_GRADIENTES = 2
EPOCAS = 20
PACIENCIA = 5
LEARNING_RATE = 1e-4
WEIGHT_DECAY = 1e-2
SEMILLA = 42
# CUDA puede reservar una fracción de la VRAM comercial de 6 GB. Se acepta una
# lectura mínima conservadora de 5.5 GiB sin relajar la lista de GPU admitidas.
MINIMO_VRAM_REPORTADA_GIB = 5.5
MINIMO_LIBRE_GIB = 4.5
MODELOS = {
    "unet_resnet34": "U-Net / ResNet34",
    "unetplusplus_resnet34": "U-Net++ / ResNet34",
    "segformer_mit_b0": "SegFormer / MIT-B0",
}
CONTEOS_ESPERADOS = {"train": 245, "val": 53, "test": 53}
COLUMNAS_HISTORIAL = [
    "modelo", "epoca", "train_loss", "train_dice", "val_loss", "val_dice",
]
COLUMNAS_EXPERIMENTOS = [
    "modelo", "arquitectura_encoder", "resolucion", "batch",
    "acumulacion_gradientes", "batch_efectivo", "learning_rate",
    "epocas_solicitadas", "epocas_ejecutadas", "mejor_epoca",
    "mejor_val_dice", "checkpoint", "estado",
]


class ErrorHandoff(RuntimeError):
    """Fallo accionable que debe detener el arnés."""


@dataclass(frozen=True)
class InformacionSistema:
    sistema: str
    version: str
    es_wsl: bool
    cuda_disponible: bool
    gpu: str
    vram_total_bytes: int
    vram_libre_bytes: int


def configuracion_conservadora() -> dict[str, object]:
    return {
        "resolucion": RESOLUCION,
        "batch_fisico": BATCH_FISICO,
        "acumulacion_gradientes": ACUMULACION_GRADIENTES,
        "amp": True,
        "epocas": EPOCAS,
        "paciencia": PACIENCIA,
        "pesos_preentrenados": True,
        "modelos": list(MODELOS),
    }


def obtener_informacion_sistema() -> InformacionSistema:
    import torch

    sistema = platform.system()
    version = platform.release()
    es_wsl = bool(os.environ.get("WSL_DISTRO_NAME")) or "microsoft" in version.lower()
    if not torch.cuda.is_available():
        return InformacionSistema(sistema, version, es_wsl, False, "", 0, 0)
    libre, total = torch.cuda.mem_get_info(0)
    return InformacionSistema(
        sistema=sistema,
        version=version,
        es_wsl=es_wsl,
        cuda_disponible=True,
        gpu=torch.cuda.get_device_name(0),
        vram_total_bytes=int(total),
        vram_libre_bytes=int(libre),
    )


def validar_entorno(
    info: InformacionSistema,
    ruta: Path,
    *,
    permitir_no_windows_en_pruebas: bool = False,
) -> None:
    ruta_texto = str(ruta).replace("\\", "/").lower()
    if info.es_wsl or ruta_texto.startswith("/mnt/") or ruta_texto.startswith("//wsl$/"):
        raise ErrorHandoff("WSL y sus rutas están prohibidos. Use PowerShell en Windows nativo.")
    if info.sistema.lower() != "windows" and not permitir_no_windows_en_pruebas:
        raise ErrorHandoff("Esta ejecución requiere Windows nativo; no use Linux ni WSL.")
    if not info.cuda_disponible:
        raise ErrorHandoff(
            "PyTorch no detecta CUDA. Revise el controlador NVIDIA y la instalación antes de continuar."
        )
    gpu = info.gpu.lower()
    if "rtx 4050 laptop" not in gpu and "rtx 4060 laptop" not in gpu:
        raise ErrorHandoff(
            f"GPU no admitida: {info.gpu or 'sin nombre'}. Se requiere RTX 4050 Laptop o RTX 4060 Laptop."
        )
    gib = 1024**3
    total_gib = info.vram_total_bytes / gib
    libre_gib = info.vram_libre_bytes / gib
    if total_gib < MINIMO_VRAM_REPORTADA_GIB:
        raise ErrorHandoff(
            f"VRAM insuficiente: CUDA reporta {total_gib:.2f} GiB; se requieren al menos "
            "5.5 GiB reportados para admitir la RTX 4050 Laptop comercial de 6 GB."
        )
    minimo_libre = max(MINIMO_LIBRE_GIB, total_gib * 0.70)
    if libre_gib < minimo_libre:
        raise ErrorHandoff(
            f"Memoria GPU libre insuficiente: {libre_gib:.2f} GiB; cierre aplicaciones hasta disponer "
            f"de al menos {minimo_libre:.2f} GiB."
        )


def validar_datos(raiz: Path = RAIZ) -> tuple[pd.DataFrame, pd.DataFrame]:
    datos = raiz / "data"
    ruta_train = datos / "train.csv"
    ruta_splits = datos / "splits.csv"
    ruta_imagenes = datos / "train_images"
    faltantes = [ruta for ruta in (ruta_train, ruta_splits, ruta_imagenes) if not ruta.exists()]
    if faltantes:
        raise ErrorHandoff("Faltan datos requeridos: " + ", ".join(str(ruta) for ruta in faltantes))

    train = pd.read_csv(ruta_train)
    splits = pd.read_csv(ruta_splits)
    if len(train) != 351:
        raise ErrorHandoff(f"data/train.csv debe contener 351 filas; contiene {len(train)}.")
    requeridas_train = {"id", "organ", "rle", "pixel_size"}
    requeridas_splits = {"id", "organ", "split"}
    if not requeridas_train.issubset(train.columns) or not requeridas_splits.issubset(splits.columns):
        raise ErrorHandoff("Los CSV no contienen las columnas requeridas por el pipeline.")
    if train["id"].duplicated().any() or splits["id"].duplicated().any():
        raise ErrorHandoff("Los identificadores de train.csv y splits.csv deben ser únicos.")
    conteos = splits["split"].value_counts().to_dict()
    if conteos != CONTEOS_ESPERADOS:
        raise ErrorHandoff(f"Conteos de splits inválidos: {conteos}; se esperaba {CONTEOS_ESPERADOS}.")
    if len(splits) != 351 or set(train["id"].astype(str)) != set(splits["id"].astype(str)):
        raise ErrorHandoff("splits.csv debe contener exactamente los mismos 351 ids de train.csv.")

    imagenes = list(ruta_imagenes.glob("*.tiff"))
    if len(imagenes) != 351:
        raise ErrorHandoff(f"data/train_images debe contener 351 archivos .tiff; contiene {len(imagenes)}.")
    if {ruta.stem for ruta in imagenes} != set(train["id"].astype(str)):
        raise ErrorHandoff("Los nombres de las imágenes no coinciden con los ids de train.csv.")
    return train, splits


def _escribir_json_atomico(ruta: Path, contenido: Mapping[str, object]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_suffix(ruta.suffix + ".tmp")
    temporal.write_text(json.dumps(contenido, ensure_ascii=False, indent=2), encoding="utf-8")
    temporal.replace(ruta)


def _escribir_csv_atomico(tabla: pd.DataFrame, ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_suffix(ruta.suffix + ".tmp")
    tabla.to_csv(temporal, index=False)
    temporal.replace(ruta)


def verificar(raiz: Path = RAIZ, info: InformacionSistema | None = None) -> dict[str, object]:
    info = info or obtener_informacion_sistema()
    validar_entorno(info, raiz)
    validar_datos(raiz)
    return {
        "estado": "correcto",
        "etapa": "verify",
        "sistema": asdict(info),
        "configuracion": configuracion_conservadora(),
        "datos": {"total": 351, **CONTEOS_ESPERADOS},
    }


def ejecutar_preflight(raiz: Path = RAIZ) -> dict[str, object]:
    info = obtener_informacion_sistema()
    verificar(raiz, info)
    from src.models import crear_modelo
    from src.training import ejecutar_preflight_cuda

    print("Ejecutando preflight CUDA real para los tres modelos...", flush=True)
    resultados = ejecutar_preflight_cuda(
        MODELOS,
        lambda nombre: crear_modelo(nombre, pesos_preentrenados=True),
        resolucion=RESOLUCION,
        batch_size=BATCH_FISICO,
        learning_rate=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
        amp=True,
    )
    return {
        "estado": "correcto",
        "etapa": "preflight",
        "sistema": asdict(info),
        "configuracion": configuracion_conservadora(),
        "resultados": resultados.to_dict(orient="records"),
    }


def _validar_cache(cache: Path, ids: set[str]) -> None:
    faltantes = [identificador for identificador in ids if not (cache / f"{identificador}.png").is_file()]
    faltantes += [
        identificador for identificador in ids if not (cache / f"{identificador}_mask.png").is_file()
    ]
    if faltantes:
        raise ErrorHandoff(
            f"La caché de 384 px quedó incompleta ({len(faltantes)} archivos faltantes). "
            "Revise espacio en disco y el log de Train."
        )


def entrenar(raiz: Path = RAIZ) -> dict[str, object]:
    info = obtener_informacion_sistema()
    verificar(raiz, info)
    import torch
    from src import preprocess as pp
    from src.models import crear_modelo
    from src.training import entrenar_modelo

    train, splits = validar_datos(raiz)
    cache = raiz / "data" / f"cache_{RESOLUCION}"
    artefactos = raiz / "data" / "artefactos_entrenamiento"
    print("Preparando o comprobando la caché de 384 px...", flush=True)
    pp.preparar_cache(train, raiz / "data" / "train_images", cache, size=RESOLUCION)
    _validar_cache(cache, set(train["id"].astype(str)))
    cargadores = pp.crear_dataloaders(
        splits,
        cache,
        size=RESOLUCION,
        batch_size=BATCH_FISICO,
        num_workers=2,
        drop_last_train=False,
    )
    cargador_train = cargadores["train"]
    cargador_val = cargadores["val"]

    historiales: list[pd.DataFrame] = []
    registros: list[dict[str, object]] = []
    for nombre, arquitectura in MODELOS.items():
        modelo = None
        try:
            print(f"Iniciando entrenamiento secuencial: {nombre}", flush=True)
            modelo = crear_modelo(nombre, pesos_preentrenados=True)
            checkpoint = artefactos / "checkpoints" / f"{nombre}.pt"
            resultado = entrenar_modelo(
                modelo,
                cargador_train,
                cargador_val,
                ruta_checkpoint=checkpoint,
                epocas=EPOCAS,
                paciencia=PACIENCIA,
                learning_rate=LEARNING_RATE,
                weight_decay=WEIGHT_DECAY,
                dispositivo="cuda",
                amp=True,
                seed=SEMILLA,
                acumulacion_gradientes=ACUMULACION_GRADIENTES,
            )
            historiales.append(resultado.historial.assign(modelo=nombre)[COLUMNAS_HISTORIAL])
            registros.append({
                "modelo": nombre,
                "arquitectura_encoder": arquitectura,
                "resolucion": RESOLUCION,
                "batch": BATCH_FISICO,
                "acumulacion_gradientes": ACUMULACION_GRADIENTES,
                "batch_efectivo": BATCH_FISICO * ACUMULACION_GRADIENTES,
                "learning_rate": LEARNING_RATE,
                "epocas_solicitadas": EPOCAS,
                "epocas_ejecutadas": len(resultado.historial),
                "mejor_epoca": resultado.mejor_epoca,
                "mejor_val_dice": resultado.mejor_val_dice,
                "checkpoint": str(resultado.ruta_checkpoint),
                "estado": "detencion_temprana" if resultado.detencion_temprana else "completado",
            })
            _escribir_csv_atomico(pd.concat(historiales, ignore_index=True), artefactos / "historial_modelos.csv")
            _escribir_csv_atomico(pd.DataFrame(registros, columns=COLUMNAS_EXPERIMENTOS), artefactos / "experimentos_modelos.csv")
            print(f"Modelo completado: {nombre}", flush=True)
        finally:
            if modelo is not None:
                try:
                    modelo.to("cpu")
                except RuntimeError:
                    pass
            del modelo
            gc.collect()
            torch.cuda.empty_cache()

    return {
        "estado": "correcto",
        "etapa": "train",
        "configuracion": configuracion_conservadora(),
        "modelos_completados": list(MODELOS),
        "artefactos": str(artefactos),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("modo", choices=("verify", "preflight", "train"))
    parser.add_argument("--resultado", type=Path, help="Ruta interna del arnés para evidencia JSON.")
    argumentos = parser.parse_args(argv)
    acciones = {"verify": verificar, "preflight": ejecutar_preflight, "train": entrenar}
    try:
        resultado = acciones[argumentos.modo]()
        if argumentos.resultado:
            _escribir_json_atomico(argumentos.resultado, resultado)
        print(json.dumps(resultado, ensure_ascii=False, indent=2), flush=True)
        return 0
    except (ErrorHandoff, FileNotFoundError, RuntimeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
