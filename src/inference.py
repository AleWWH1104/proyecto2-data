"""Bounded inference on new uploads; no dataset access or accuracy estimation."""

from dataclasses import dataclass
from io import BytesIO
import time
import warnings
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
import tifffile
import torch

from src import preprocess as pp
from src.evaluation import cargar_modelo_entrenado
from src.models import FABRICAS_MODELOS
from src.training import adaptar_logits

MAX_UPLOAD_BYTES = 64 * 1024 * 1024
MAX_PIXELS = 9_000_000
MAX_SIDE = 8192
THRESHOLD = 0.5


class InferenceError(ValueError):
    """An input or model contract failed before producing a usable result."""


def _validate_dimensions(height, width):
    if min(height, width) < 2 or max(height, width) > MAX_SIDE:
        raise InferenceError("Las dimensiones deben estar entre 2 y 8192 píxeles por lado.")
    if height * width > MAX_PIXELS:
        raise InferenceError("La imagen supera el límite de 9 millones de píxeles.")


def decode_upload(content: bytes) -> np.ndarray:
    """Decode single-frame PNG/JPEG/TIFF, checking budgets before allocation.

    uint16 values use the existing pipeline's global min/max scaling, including
    constant images mapping to zero. TIFF axes must describe a single 2D image.
    Alpha is dropped, not composited, matching a_rgb_uint8.
    """
    if not content or len(content) > MAX_UPLOAD_BYTES:
        raise InferenceError("El archivo debe contener una imagen y no superar 64 MiB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(content)) as header:
                if header.format not in {"PNG", "JPEG", "TIFF"}:
                    raise InferenceError("Formato no admitido. Use PNG, JPEG o TIFF.")
                _validate_dimensions(header.height, header.width)
                if getattr(header, "n_frames", 1) != 1:
                    raise InferenceError("Use una sola imagen, no una animación o TIFF multipágina.")
                if header.format == "TIFF":
                    with tifffile.TiffFile(BytesIO(content)) as tiff:
                        if len(tiff.series) != 1:
                            raise InferenceError("El TIFF debe contener una sola serie 2D.")
                        series = tiff.series[0]
                        axes = series.axes
                        if axes not in {"YX", "YXS", "SYX"}:
                            raise InferenceError("El TIFF no representa una imagen 2D compatible.")
                        shape = dict(zip(axes, series.shape))
                        _validate_dimensions(shape["Y"], shape["X"])
                        if shape.get("S", 1) not in {1, 3, 4}:
                            raise InferenceError("El TIFF debe tener 1, 3 o 4 canales.")
                        if series.dtype.kind != "u" or series.dtype.itemsize not in {1, 2}:
                            raise InferenceError("El TIFF debe usar enteros sin signo de 8 o 16 bits.")
                        # Preserve 16-bit RGB values; Pillow's RGB conversion loses them.
                        raw = series.asarray()
                        if axes == "SYX":
                            raw = raw.transpose(1, 2, 0)
                        if raw.ndim == 3 and raw.shape[-1] == 1:
                            raw = raw[..., 0]
                        if raw.ndim == 3 and int(tiff.pages[0].photometric) != 2:
                            raise InferenceError("El TIFF multicanal debe ser RGB.")
                        if raw.ndim == 2 and int(tiff.pages[0].photometric) not in {0, 1}:
                            raise InferenceError("El TIFF monocanal debe representar escala de grises.")
                        if raw.ndim == 2 and int(tiff.pages[0].photometric) == 0:
                            raw = np.iinfo(raw.dtype).max - raw
                elif header.mode in {"I", "I;16", "I;16B", "I;16L"}:
                    raw = np.asarray(header)
                    if raw.min() < 0 or raw.max() > 65535:
                        raise InferenceError("Los valores de la imagen exceden el rango de 16 bits.")
                    raw = raw.astype(np.uint16)
                else:
                    if header.format == "PNG" and content[24] == 16:
                        raise InferenceError("Para RGB de 16 bits use TIFF; PNG RGB de 16 bits no es compatible.")
                    raw = np.asarray(header.convert("RGB"))
        rgb = pp.a_rgb_uint8(raw)
        if rgb.ndim != 3 or rgb.shape[2] != 3:
            raise InferenceError("La imagen no se pudo convertir a RGB.")
        _validate_dimensions(*rgb.shape[:2])
        return rgb
    except InferenceError:
        raise
    except Exception as error:
        raise InferenceError("No se pudo decodificar la imagen. Revise el archivo y su formato.") from error


def prepare_tensor(rgb: np.ndarray) -> torch.Tensor:
    """Reproduce cache resize followed by validation normalization at 384 px."""
    if rgb.dtype != np.uint8 or rgb.ndim != 3 or rgb.shape[2] != 3:
        raise InferenceError("Se requiere una imagen RGB de 8 bits.")
    _validate_dimensions(*rgb.shape[:2])
    # Uploaded pixel spacing is unknown: assume the HPA reference (0.4 µm/px).
    cached = pp.redimensionar(rgb, pp.IMG_SIZE)
    normalized = pp.transformaciones("val", pp.IMG_SIZE)(image=cached)["image"]
    tensor = torch.from_numpy(np.ascontiguousarray(normalized.transpose(2, 0, 1)))
    return tensor.float().unsqueeze(0)


def available_checkpoints(directory: Path) -> dict[str, Path]:
    return {
        name: Path(directory) / f"{name}.pt"
        for name in FABRICAS_MODELOS
        if (Path(directory) / f"{name}.pt").is_file()
    }


def load_model(name: str, checkpoint: Path):
    """Load repository-managed weights only, strictly, on CPU without downloads."""
    if name not in FABRICAS_MODELOS:
        raise InferenceError("Modelo no reconocido.")
    if not Path(checkpoint).is_file():
        raise InferenceError(f"Falta el checkpoint de {name}. No se generó una predicción.")
    try:
        model, _ = cargar_modelo_entrenado(name, checkpoint, "cpu")
        return model
    except Exception as error:
        raise InferenceError(f"El checkpoint de {name} es incompatible o no se pudo cargar.") from error


@dataclass
class Prediction:
    mask: np.ndarray
    overlay: np.ndarray
    probabilities: np.ndarray
    seconds: float
    coverage_percent: float


@torch.inference_mode()
def predict(model, rgb: np.ndarray) -> Prediction:
    tensor = prepare_tensor(rgb)
    model.to("cpu").eval()
    start = time.perf_counter()
    output = model(tensor)
    elapsed = time.perf_counter() - start
    # Same logit alignment as evaluation, before sigmoid and thresholding.
    logits = adaptar_logits(output, torch.empty(1, 1, pp.IMG_SIZE, pp.IMG_SIZE))
    if not torch.isfinite(logits).all():
        raise InferenceError("El modelo produjo valores no finitos.")
    probabilities = torch.sigmoid(logits)[0, 0].cpu().numpy()
    mask384 = (probabilities >= THRESHOLD).astype(np.uint8)
    height, width = rgb.shape[:2]
    # Restore the evaluated binary mask, without changing threshold semantics.
    mask = cv2.resize(mask384, (width, height), interpolation=cv2.INTER_NEAREST)
    overlay = rgb.copy()
    selected = mask.astype(bool)
    overlay[selected] = (
        0.55 * rgb[selected] + 0.45 * np.array([0, 229, 255])
    ).astype(np.uint8)
    return Prediction(mask, overlay, probabilities, elapsed, float(mask.mean() * 100))
