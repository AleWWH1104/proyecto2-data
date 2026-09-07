# Proyecto 2 – Análisis Exploratorio

**Data Science**

**Reto 18: Hackeando el cuerpo humano** — [HuBMAP - Hacking the Human Body](https://www.kaggle.com/competitions/hubmap-organ-segmentation) (Visión Artificial: segmentación de estructuras tisulares funcionales en imágenes de órganos humanos).

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

## División de actividades

Las secciones del notebook siguen la numeración de la guía. Cada quien completa sus secciones por completo antes de que empiece la siguiente, y hace su propio commit al terminar.

- **Persona 1** — 1, 2, 3 y 4.a: investigación del tema, situación problemática, problema científico, objetivos, descripción de los datos, limpieza, y descripción de variables/observaciones.
- **Persona 2** — 4.b y 4.c: resumen de variables numéricas, tablas de frecuencia de categóricas, cruce de variables importantes, correlaciones, outliers y valores faltantes.
- **Persona 3** — 4.d y 5: gráficos exploratorios (univariados y con imágenes) y conclusiones.
