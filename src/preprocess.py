"""Preprocesamiento de imágenes y máscaras para la segmentación de FTU (Reto 18, HuBMAP).

Este módulo lo usan el notebook de resultados (entrenamiento y evaluación) y, más adelante,
la aplicación. Así una imagen nueva pasa exactamente por los mismos pasos que las de
entrenamiento sin que el usuario tenga que hacer nada.
"""

from pathlib import Path

import albumentations as A
import cv2
import numpy as np
import pandas as pd
import tifffile
import torch
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Dataset

# Todas las imágenes de entrenamiento vienen de HPA con 0.4 µm por píxel.
PIXEL_SIZE_REF = 0.4
IMG_SIZE = 768
SEED = 42

ORGANOS = ["kidney", "prostate", "largeintestine", "spleen", "lung"]

# Media y desviación de ImageNet: los encoders de los tres modelos vienen preentrenados ahí.
MEAN = (0.485, 0.456, 0.406)
STD = (0.229, 0.224, 0.225)


# ---------------------------------------------------------------
# Máscaras RLE
# ---------------------------------------------------------------

def rle_decode(rle, shape):
    """Decodifica una máscara RLE a un array binario (alto, ancho).

    En esta competencia los píxeles se numeran de arriba hacia abajo y luego de izquierda
    a derecha (orden por columnas), por eso se reconstruye con order="F".
    """
    alto, ancho = shape
    mask = np.zeros(alto * ancho, dtype=np.uint8)
    if isinstance(rle, str) and rle.strip():
        s = np.asarray(rle.split(), dtype=np.int64)
        inicios, largos = s[0::2] - 1, s[1::2]
        for lo, n in zip(inicios, largos):
            mask[lo:lo + n] = 1
    return mask.reshape((alto, ancho), order="F")


def rle_encode(mask):
    """Codifica una máscara binaria (alto, ancho) al formato RLE de la competencia."""
    pixeles = np.concatenate([[0], mask.flatten(order="F").astype(np.uint8), [0]])
    runs = np.where(pixeles[1:] != pixeles[:-1])[0] + 1
    runs[1::2] -= runs[::2]
    return " ".join(str(x) for x in runs)


# ---------------------------------------------------------------
# Lectura y redimensionamiento
# ---------------------------------------------------------------

def leer_imagen(ruta):
    """Lee una imagen .tiff (o .png/.jpg) y la devuelve como RGB uint8 (alto, ancho, 3)."""
    ruta = Path(ruta)
    if ruta.suffix.lower() in (".tif", ".tiff"):
        img = tifffile.imread(ruta)
    else:
        img = cv2.cvtColor(cv2.imread(str(ruta), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
    return a_rgb_uint8(img)


def a_rgb_uint8(img):
    """Normaliza el formato de una imagen: canales al final, 3 canales y tipo uint8."""
    img = np.asarray(img)
    img = np.squeeze(img)
    if img.ndim == 3 and img.shape[0] in (3, 4) and img.shape[-1] not in (3, 4):
        img = np.transpose(img, (1, 2, 0))
    if img.ndim == 2:
        img = np.stack([img] * 3, axis=-1)
    img = img[..., :3]
    if img.dtype != np.uint8:
        img = img.astype(np.float32)
        img = 255 * (img - img.min()) / max(float(img.max() - img.min()), 1e-6)
        img = img.astype(np.uint8)
    return np.ascontiguousarray(img)


def ajustar_tamano_pixel(img, pixel_size, ref=PIXEL_SIZE_REF, es_mascara=False):
    """Reescala una imagen para que su tamaño de píxel coincida con el de entrenamiento.

    Una imagen con píxeles de 0.8 µm se amplía al doble para que las FTU tengan el
    mismo tamaño en píxeles que en las imágenes de HPA (0.4 µm).
    """
    escala = pixel_size / ref
    if np.isclose(escala, 1.0):
        return img
    alto, ancho = img.shape[:2]
    nuevo = (max(1, round(ancho * escala)), max(1, round(alto * escala)))
    return redimensionar(img, nuevo, es_mascara)


def redimensionar(img, size, es_mascara=False):
    """Redimensiona a size (int para cuadrado, o tupla (ancho, alto))."""
    if isinstance(size, int):
        size = (size, size)
    if es_mascara:
        return cv2.resize(img, size, interpolation=cv2.INTER_NEAREST)
    reduce = size[0] < img.shape[1]
    return cv2.resize(img, size, interpolation=cv2.INTER_AREA if reduce else cv2.INTER_LINEAR)


def preparar_cache(df, img_dir, cache_dir, size=IMG_SIZE):
    """Guarda cada imagen y su máscara ya redimensionadas como .png.

    Leer un .tiff de 3000x3000 px en cada época es muy lento; con la caché solo se
    hace una vez. Si un archivo ya existe no se vuelve a generar.
    """
    img_dir, cache_dir = Path(img_dir), Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    for fila in df.itertuples():
        ruta_img = cache_dir / f"{fila.id}.png"
        ruta_mask = cache_dir / f"{fila.id}_mask.png"
        if ruta_img.exists() and ruta_mask.exists():
            continue
        img = leer_imagen(img_dir / f"{fila.id}.tiff")
        mask = rle_decode(fila.rle, img.shape[:2])
        img = ajustar_tamano_pixel(img, fila.pixel_size)
        mask = ajustar_tamano_pixel(mask, fila.pixel_size, es_mascara=True)
        cv2.imwrite(str(ruta_img), cv2.cvtColor(redimensionar(img, size), cv2.COLOR_RGB2BGR))
        cv2.imwrite(str(ruta_mask), redimensionar(mask, size, es_mascara=True))
    return cache_dir


# ---------------------------------------------------------------
# División de los datos
# ---------------------------------------------------------------

def crear_splits(df, val=0.15, test=0.15, seed=SEED):
    """Divide en entrenamiento, validación y prueba manteniendo la proporción de cada órgano."""
    ids_train, ids_resto = train_test_split(
        df, test_size=val + test, stratify=df["organ"], random_state=seed
    )
    ids_val, ids_test = train_test_split(
        ids_resto, test_size=test / (val + test), stratify=ids_resto["organ"], random_state=seed
    )
    splits = pd.concat([
        ids_train[["id", "organ"]].assign(split="train"),
        ids_val[["id", "organ"]].assign(split="val"),
        ids_test[["id", "organ"]].assign(split="test"),
    ])
    return splits.sort_values("id").reset_index(drop=True)


# ---------------------------------------------------------------
# Data augmentation
# ---------------------------------------------------------------

def transformaciones(split, size=IMG_SIZE):
    """Transformaciones de albumentations según el conjunto.

    En entrenamiento se usan transformaciones geométricas (el tejido no tiene una
    orientación fija) y de color, que simulan las diferencias de tinción entre
    laboratorios (Tellez et al., 2019). Validación y prueba solo se normalizan.
    """
    finales = [A.Resize(size, size), A.Normalize(mean=MEAN, std=STD)]
    if split != "train":
        return A.Compose(finales)
    return A.Compose([
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.5),
        A.RandomRotate90(p=0.5),
        A.Affine(scale=(0.8, 1.2), rotate=(-30, 30), p=0.5),
        A.HueSaturationValue(hue_shift_limit=15, sat_shift_limit=25, val_shift_limit=15, p=0.5),
        A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.5),
        A.RandomGamma(p=0.3),
        A.GaussianBlur(blur_limit=(3, 5), p=0.2),
        *finales,
    ])


# ---------------------------------------------------------------
# Dataset y DataLoaders de PyTorch
# ---------------------------------------------------------------

class HubmapDataset(Dataset):
    """Devuelve la imagen (3, H, W), la máscara (1, H, W), el órgano y el id.

    Lee las imágenes ya redimensionadas de la caché que genera preparar_cache.
    """

    def __init__(self, df, cache_dir, transform=None):
        self.df = df.reset_index(drop=True)
        self.cache_dir = Path(cache_dir)
        self.transform = transform

    def __len__(self):
        return len(self.df)

    def __getitem__(self, i):
        fila = self.df.iloc[i]
        img = cv2.cvtColor(cv2.imread(str(self.cache_dir / f"{fila['id']}.png")), cv2.COLOR_BGR2RGB)
        mask = cv2.imread(str(self.cache_dir / f"{fila['id']}_mask.png"), cv2.IMREAD_GRAYSCALE)
        if self.transform is not None:
            out = self.transform(image=img, mask=mask)
            img, mask = out["image"], out["mask"]
        return {
            "image": torch.from_numpy(np.ascontiguousarray(img.transpose(2, 0, 1))).float(),
            "mask": torch.from_numpy(np.ascontiguousarray(mask[None])).float(),
            "organ": fila["organ"],
            "id": int(fila["id"]),
        }


def crear_dataloaders(splits, cache_dir, size=IMG_SIZE, batch_size=8, num_workers=2):
    """Crea un DataLoader por conjunto a partir del DataFrame de splits."""
    loaders = {}
    for split in ("train", "val", "test"):
        ds = HubmapDataset(splits[splits["split"] == split], cache_dir, transformaciones(split, size))
        loaders[split] = DataLoader(
            ds,
            batch_size=batch_size,
            shuffle=(split == "train"),
            drop_last=(split == "train"),
            num_workers=num_workers,
            pin_memory=torch.cuda.is_available(),
        )
    return loaders


# ---------------------------------------------------------------
# Inferencia sobre una imagen nueva (lo usará la aplicación)
# ---------------------------------------------------------------

def preprocesar_para_modelo(img, pixel_size=PIXEL_SIZE_REF, size=IMG_SIZE):
    """Convierte una imagen cualquiera en el tensor (1, 3, size, size) que esperan los modelos.

    Devuelve también el tamaño original, que se necesita para regresar la predicción
    a la resolución de la imagen de entrada.
    """
    img = a_rgb_uint8(img)
    tamano_original = img.shape[:2]
    img = ajustar_tamano_pixel(img, pixel_size)
    img = transformaciones("test", size)(image=img)["image"]
    tensor = torch.from_numpy(img.transpose(2, 0, 1)).float().unsqueeze(0)
    return tensor, tamano_original


def postprocesar(probabilidades, tamano_original, umbral=0.5):
    """Lleva el mapa de probabilidades del modelo a una máscara binaria del tamaño original."""
    if isinstance(probabilidades, torch.Tensor):
        probabilidades = probabilidades.detach().cpu().numpy()
    prob = np.squeeze(probabilidades).astype(np.float32)
    alto, ancho = tamano_original
    prob = cv2.resize(prob, (ancho, alto), interpolation=cv2.INTER_LINEAR)
    return (prob > umbral).astype(np.uint8)
