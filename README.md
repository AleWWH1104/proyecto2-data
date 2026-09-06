# Proyecto 2 – Análisis Exploratorio
**CC3084 – Data Science | UVG | Semestre II 2026**

**Reto 18: Hackeando el cuerpo humano** — [HuBMAP - Hacking the Human Body](https://www.kaggle.com/competitions/hubmap-organ-segmentation) (Visión Artificial: segmentación de estructuras tisulares funcionales en imágenes de órganos humanos).

## Estructura del proyecto

Todo el trabajo (código, gráficos, interpretaciones y conclusiones) vive en **un solo notebook**:

```
proyecto2-data/
├── EDA_Reto18.ipynb   ← notebook único: aquí va todo
├── data/               ← csv/imágenes de Kaggle (NO se sube a git)
├── docs/               ← guía del proyecto (pdf)
└── README.md
```

No hay carpeta `src/`: todo el código va directo en las celdas del notebook, junto a su título e interpretación en Markdown.

## Datos

Descarga desde la competencia de Kaggle (hay que aceptar las reglas primero: botón **"Join Competition"** en la página de la competencia — es gratis e instantáneo):

- `train.csv` — es el único archivo necesario, aquí está casi todo el EDA (órgano, sexo, edad, tamaño de píxel, grosor de tejido, dimensiones de imagen). No hace falta `test.csv` ni `sample_submission.csv` porque no se va a participar en la competencia, solo se usan los datos.
- `train_images/`, `test_images/` — **no descargues todo el set** (son archivos `.tiff` pesados y no hacen falta para el EDA). Basta con bajar una **muestra pequeña** (10-20 imágenes, idealmente variadas por órgano) para mostrar ejemplos visuales del problema y las máscaras — eso sí requiere haber aceptado las reglas de la competencia.

Coloca lo descargado dentro de `data/` (esa carpeta está en `.gitignore`, no se versiona).

Con la [Kaggle API](https://www.kaggle.com/docs/api) (requiere `kaggle.json` configurado):
```bash
kaggle competitions download -c hubmap-organ-segmentation -f train.csv -p data/
```

## División de actividades (3 personas, secciones secuenciales)

Las secciones del notebook están numeradas igual que las actividades de la guía (1, 2, 3, 4.a-4.d, 5). Cada persona completa sus secciones por completo (código + interpretación + gráficos) antes de que empiece la siguiente, y hace su propio commit al terminar (esto también sirve para que la evaluación individual por contribuciones en GitHub sea clara).

### Persona 1 — Secciones 1, 2, 3 y 4.a
- **1. Investigación del tema:** qué es HuBMAP, qué son las FTUs (unidades funcionales de tejido), qué órganos incluye el dataset, cómo se obtienen y tiñen las imágenes, por qué importa segmentarlas.
- **2. Análisis del problema planteado y los datos:** situación problemática, problema científico, objetivos (1 general + 2 específicos), descripción general de los datos.
- **3. Limpieza y preprocesamiento:** nulos, duplicados, tipos, decodificación de las máscaras RLE si aplica.
- **4.a Variables y observaciones disponibles:** cuántas variables/observaciones hay, tipo de cada variable.

### Persona 2 — Sección 4.b
- **4.b Resumen de variables numéricas y tablas de frecuencia de categóricas:** estadística descriptiva (edad, tamaño de píxel, grosor de tejido, alto/ancho de imagen) y tablas de frecuencia/proporciones (órgano, fuente de datos, sexo).

### Persona 3 — Secciones 4.c, 4.d y 5
- **4.c Cruce de variables importantes:** cruce de variables clave (ej. órgano vs. edad/sexo/grosor de tejido), correlaciones entre numéricas, outliers y valores faltantes.
- **4.d Gráficos exploratorios:** gráficos univariados (histogramas, boxplots, barras) y EDA visual de imágenes (ejemplos de tejido por órgano, máscaras superpuestas sobre la muestra descargada).
- **5. Conclusiones:** resumen de hallazgos y próximos pasos.

## Entregables (según guía)
- PDF del informe (exportado del notebook).
- Link de este repositorio.
- Presentación en PowerPoint.
- **Fecha límite:** 11 de septiembre de 2025.
