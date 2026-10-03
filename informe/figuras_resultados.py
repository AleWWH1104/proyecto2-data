"""Figuras de la sección 4 a partir de metrics.csv y del historial de entrenamiento.

Se corre desde la raíz del repositorio: uv run python -m informe.figuras_resultados
"""

from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from matplotlib.lines import Line2D

from src import preprocess as pp
from src.evaluation import cargar_modelo_entrenado
from src.training import adaptar_logits

DATA = Path("data")
ARTEFACTOS = DATA / "artefactos_entrenamiento"
OUT = Path("informe/figuras")

MODELOS = {
    "unet_resnet34": "U-Net",
    "unetplusplus_resnet34": "U-Net++",
    "segformer_mit_b0": "SegFormer",
}
COLORES = {
    "unet_resnet34": "#2a78d6",
    "unetplusplus_resnet34": "#eb6834",
    "segformer_mit_b0": "#1baf7a",
}
CIAN = "#00e5ff"
TEXTO = "#52514e"


def _estilo(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#b5b4ae")
    ax.tick_params(colors=TEXTO)
    ax.grid(axis="y", color="#e6e5e0", linewidth=0.8)
    ax.set_axisbelow(True)


def _guardar(fig, nombre, dpi=150):
    if nombre:
        OUT.mkdir(parents=True, exist_ok=True)
        fig.savefig(OUT / nombre, dpi=dpi, bbox_inches="tight")
    return fig


def comparacion_modelos(metricas, nombre="resultados_modelos.png"):
    """Dice e IoU promedio de cada modelo en el conjunto de prueba."""
    resumen = metricas.groupby("modelo")[["dice", "iou"]].mean().loc[list(MODELOS)]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    for ax, metrica, titulo in zip(axes, ["dice", "iou"], ["Dice", "IoU"]):
        barras = ax.bar(
            [MODELOS[m] for m in resumen.index], resumen[metrica],
            color=[COLORES[m] for m in resumen.index], width=0.6,
            edgecolor="white", linewidth=2,
        )
        ax.bar_label(barras, fmt="%.3f", padding=3, color="#0b0b0b")
        ax.set_title(f"{titulo} promedio")
        ax.set_ylim(0, 1)
        _estilo(ax)
    fig.suptitle(f"Comparación de modelos ({metricas['id'].nunique()} imágenes de prueba)")
    fig.tight_layout()
    return _guardar(fig, nombre)


def dice_por_organo(metricas, nombre="resultados_organos.png"):
    """Dice promedio por órgano para cada modelo."""
    tabla = metricas.pivot_table(index="organ", columns="modelo", values="dice", aggfunc="mean")
    conteo = metricas.drop_duplicates("id")["organ"].value_counts()
    organos = list(conteo.index)
    x = np.arange(len(organos))
    ancho = 0.26

    fig, ax = plt.subplots(figsize=(11, 4.5))
    for i, modelo in enumerate(MODELOS):
        ax.bar(
            x + (i - 1) * ancho, tabla.loc[organos, modelo], ancho,
            color=COLORES[modelo], label=MODELOS[modelo], edgecolor="white", linewidth=2,
        )
    ax.set_xticks(x, [f"{o}\n(n={conteo[o]})" for o in organos])
    ax.set_ylim(0, 1)
    ax.set_ylabel("Dice promedio")
    ax.set_title("Dice por órgano en el conjunto de prueba")
    ax.legend(frameon=False, ncol=3, loc="upper right")
    _estilo(ax)
    fig.tight_layout()
    return _guardar(fig, nombre)


def curvas_entrenamiento(historial, nombre="resultados_curvas.png"):
    """Pérdida y Dice por época, en entrenamiento (punteada) y validación (continua)."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    for ax, metrica, titulo in zip(axes, ["loss", "dice"], ["Pérdida (Dice + BCE)", "Dice"]):
        for modelo in MODELOS:
            h = historial[historial["modelo"] == modelo]
            ax.plot(h["epoca"], h[f"train_{metrica}"], "--", color=COLORES[modelo], linewidth=2)
            ax.plot(h["epoca"], h[f"val_{metrica}"], "-", color=COLORES[modelo], linewidth=2)
            if metrica == "dice":
                mejor = h.loc[h["val_dice"].idxmax()]
                ax.plot(mejor["epoca"], mejor["val_dice"], "o", color=COLORES[modelo],
                        markersize=8, markeredgecolor="white", markeredgewidth=2)
        ax.set_title(titulo)
        ax.set_xlabel("Época")
        _estilo(ax)

    leyenda = [Line2D([], [], color=COLORES[m], linewidth=2, label=MODELOS[m]) for m in MODELOS]
    leyenda += [
        Line2D([], [], color=TEXTO, linestyle="--", label="entrenamiento"),
        Line2D([], [], color=TEXTO, linestyle="-", label="validación"),
        Line2D([], [], color=TEXTO, marker="o", linestyle="", label="mejor época"),
    ]
    fig.legend(handles=leyenda, loc="lower center", ncol=6, frameon=False, bbox_to_anchor=(0.5, -0.06))
    fig.suptitle("Curvas de entrenamiento y validación")
    fig.tight_layout()
    return _guardar(fig, nombre)


def _superponer(ax, img, mask, titulo):
    ax.imshow(img)
    ax.imshow(np.ma.masked_where(mask == 0, mask), cmap=plt.matplotlib.colors.ListedColormap([CIAN]),
              alpha=0.4, vmin=0, vmax=1)
    if mask.any():
        ax.contour(mask, levels=[0.5], colors=CIAN, linewidths=0.8)
    ax.set_title(titulo, fontsize=10)
    ax.axis("off")


def ejemplos_prediccion(metricas, cache_dir=DATA / f"cache_{pp.IMG_SIZE}",
                        checkpoints=ARTEFACTOS / "checkpoints", dispositivo="cpu",
                        nombre="resultados_ejemplos.png"):
    """Una imagen de prueba por órgano: original, máscara real y la predicción de cada modelo.

    Se elige la imagen cuyo Dice de SegFormer está más cerca de la mediana de su órgano.
    """
    seg = metricas[metricas["modelo"] == "segformer_mit_b0"].copy()
    seg["distancia"] = (seg["dice"] - seg.groupby("organ")["dice"].transform("median")).abs()
    elegidas = seg.sort_values("distancia").drop_duplicates("organ").set_index("organ").loc[pp.ORGANOS]
    dice = metricas.set_index(["modelo", "id"])["dice"]

    transform = pp.transformaciones("test")
    imagenes, mascaras, tensores = [], [], []
    for id_ in elegidas["id"]:
        img = cv2.cvtColor(cv2.imread(str(Path(cache_dir) / f"{id_}.png")), cv2.COLOR_BGR2RGB)
        mask = cv2.imread(str(Path(cache_dir) / f"{id_}_mask.png"), cv2.IMREAD_GRAYSCALE)
        imagenes.append(img)
        mascaras.append(mask)
        tensores.append(torch.from_numpy(transform(image=img)["image"].transpose(2, 0, 1)))
    lote = torch.stack(tensores).float().to(dispositivo)

    predicciones = {}
    for modelo in MODELOS:
        red, _ = cargar_modelo_entrenado(modelo, Path(checkpoints) / f"{modelo}.pt", dispositivo)
        with torch.no_grad():
            logits = adaptar_logits(red(lote), torch.zeros(len(lote), 1, *lote.shape[2:]))
        predicciones[modelo] = (torch.sigmoid(logits) >= 0.5).squeeze(1).cpu().numpy().astype(np.uint8)
        del red

    fig, axes = plt.subplots(len(elegidas), 2 + len(MODELOS), figsize=(15, 3.2 * len(elegidas)))
    for i, (organ, fila) in enumerate(elegidas.iterrows()):
        axes[i, 0].imshow(imagenes[i])
        axes[i, 0].set_title(f"{organ} · id {fila['id']}", fontsize=10)
        axes[i, 0].axis("off")
        _superponer(axes[i, 1], imagenes[i], mascaras[i], "Máscara real")
        for j, modelo in enumerate(MODELOS):
            titulo = f"{MODELOS[modelo]} · Dice {dice[(modelo, fila['id'])]:.2f}"
            _superponer(axes[i, 2 + j], imagenes[i], predicciones[modelo][i], titulo)
    fig.suptitle("Ejemplos del conjunto de prueba (FTU en cian)", y=1.0)
    fig.tight_layout(rect=(0, 0, 1, 0.985))
    return _guardar(fig, nombre, dpi=100)


if __name__ == "__main__":
    import matplotlib
    matplotlib.use("Agg")

    metricas = pd.read_csv(DATA / "metrics.csv")
    historial = pd.read_csv(ARTEFACTOS / "historial_modelos.csv")
    comparacion_modelos(metricas)
    dice_por_organo(metricas)
    curvas_entrenamiento(historial)
    ejemplos_prediccion(metricas, dispositivo="cuda" if torch.cuda.is_available() else "cpu")
    print("figuras escritas en", OUT)
