"""Fábricas de los modelos de segmentación usados en el proyecto."""

from collections.abc import Callable

from torch import nn
from segmentation_models_pytorch import Unet, UnetPlusPlus
from transformers import SegformerConfig, SegformerForSemanticSegmentation


MODELO_SEGFORMER = "nvidia/mit-b0"


def crear_unet_resnet34(pesos_preentrenados: bool = False) -> nn.Module:
    """Crea U-Net con ResNet34 y logits binarios a resolución de entrada."""

    return Unet(
        encoder_name="resnet34",
        encoder_weights="imagenet" if pesos_preentrenados else None,
        in_channels=3,
        classes=1,
        activation=None,
    )


def crear_unetplusplus_resnet34(pesos_preentrenados: bool = False) -> nn.Module:
    """Crea U-Net++ con ResNet34 y logits binarios a resolución de entrada."""

    return UnetPlusPlus(
        encoder_name="resnet34",
        encoder_weights="imagenet" if pesos_preentrenados else None,
        in_channels=3,
        classes=1,
        activation=None,
    )


def crear_segformer_mit_b0(pesos_preentrenados: bool = False) -> nn.Module:
    """Crea SegFormer MIT-B0 con una clase y sin activación final.

    Con pesos desactivados, la configuración se construye localmente y no consulta
    Hugging Face. Con pesos activados, se descarga el encoder ``nvidia/mit-b0``;
    la cabeza binaria se inicializa para este proyecto.
    """

    configuracion = SegformerConfig(
        num_labels=1,
        id2label={0: "FTU"},
        label2id={"FTU": 0},
    )
    if not pesos_preentrenados:
        return SegformerForSemanticSegmentation(configuracion)
    return SegformerForSemanticSegmentation.from_pretrained(
        MODELO_SEGFORMER,
        config=configuracion,
        ignore_mismatched_sizes=True,
    )


FABRICAS_MODELOS: dict[str, Callable[[bool], nn.Module]] = {
    "unet_resnet34": crear_unet_resnet34,
    "unetplusplus_resnet34": crear_unetplusplus_resnet34,
    "segformer_mit_b0": crear_segformer_mit_b0,
}


def crear_modelo(nombre: str, pesos_preentrenados: bool = False) -> nn.Module:
    """Crea un modelo por su nombre estable de experimento."""

    try:
        fabrica = FABRICAS_MODELOS[nombre]
    except KeyError as error:
        disponibles = ", ".join(FABRICAS_MODELOS)
        raise ValueError(f"Modelo desconocido: {nombre}. Disponibles: {disponibles}.") from error
    return fabrica(pesos_preentrenados)
