# Proyecto 2 – Análisis Exploratorio

**Data Science**

**Reto 18: Hackeando el cuerpo humano** — [HuBMAP - Hacking the Human Body](https://www.kaggle.com/competitions/hubmap-organ-segmentation) (Visión Artificial: segmentación de estructuras tisulares funcionales en imágenes de órganos humanos).

## Descripción

Análisis exploratorio de datos (EDA) sobre el dataset de la competencia HuBMAP, orientado a entender cómo están compuestas las imágenes de tejido y las variables que las acompañan (órgano, fuente, edad, sexo, tamaño y proporción de la unidad funcional de tejido), como base para una futura solución de segmentación. Incluye limpieza y preprocesamiento de los datos, análisis univariado, bivariado y multivariado, y un informe con los hallazgos principales.

## Cómo correrlo

```bash
uv sync
```

Descarga `train.csv` desde la [competencia en Kaggle](https://www.kaggle.com/competitions/hubmap-organ-segmentation/data) (hay que aceptar las reglas primero, botón "Join Competition") y colócalo en `data/`.

Para la parte de gráficos con imágenes (sección 4.d), baja también una muestra pequeña de `train_images/` (10-20 imágenes basta) y ponla en `data/train_images/`. No se necesita descargar todo el set de imágenes.

Luego abre el notebook:

```bash
uv run jupyter notebook proyecto2-reto18.ipynb
```
