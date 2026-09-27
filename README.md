# Proyecto 2 – Data Science

**Reto 18: Hackeando el cuerpo humano**. [HuBMAP - Hacking the Human Body](https://www.kaggle.com/competitions/hubmap-organ-segmentation) (Visión Artificial: segmentación de unidades funcionales de tejido, FTU, en imágenes histológicas de riñón, próstata, intestino grueso, bazo y pulmón).

Usamos los datos de la competencia de Kaggle, pero no participamos en ella: no se suben predicciones. Todo se corre en local.

## Estructura

```
proyecto2-reto18.ipynb       Fase 1: análisis exploratorio (entregado)
proyecto2-resultados.ipynb   Fase 2: preprocesamiento, modelos y evaluación
src/preprocess.py            Pipeline de datos compartido (notebook y, después, la app)
data/
  train.csv                  Se descarga de Kaggle (no se sube al repo)
  train_images/              Se descarga de Kaggle (no se sube al repo)
  splits.csv                 División train/val/test (SÍ se sube: todos usan la misma)
  cache_768/                 La genera el notebook (no se sube al repo)
docs/
  division_avances_resultados.md   Qué hace cada persona en esta fase
informe/                     Informe en LaTeX, figuras y referencias.bib
presentacion/                Presentación en Beamer
```

## Cómo correrlo

### 1. Instalar dependencias

```bash
uv sync
```

Hay que correrlo **cada vez que hagas pull** y cambie `pyproject.toml`, porque en esta fase se agregaron librerías (`torch`, `albumentations`, `opencv`, `tifffile`, `scikit-learn`). Si falta alguna, el notebook falla en la primera celda.

### 2. Descargar los datos

En la [página de datos de la competencia](https://www.kaggle.com/competitions/hubmap-organ-segmentation/data) (hay que aceptar las reglas con el botón "Join Competition"; esto solo habilita la descarga) baja:

- `train.csv` → `data/train.csv`
- la carpeta **`train_images/` completa** (351 imágenes `.tiff`, ~5.8 GB) → `data/train_images/`

Debe quedar así:

```
data/
  train.csv
  splits.csv
  train_images/
    10044.tiff
    10274.tiff
    ...           (351 archivos)
```

El notebook del análisis exploratorio solo necesita `train.csv`. El de resultados necesita **todas** las imágenes.

### 3. Abrir el notebook

```bash
uv run jupyter notebook proyecto2-resultados.ipynb
```

Corre todas las celdas desde el inicio (Run All). La primera celda debe imprimir `Imágenes disponibles: True`; si dice `False`, revisa que las imágenes estén en `data/train_images/`.

La primera vez, la sección 2.2 genera `data/cache_768/` con las imágenes redimensionadas. Tarda unos minutos y solo se hace una vez.

## Fase 2: Resultados (trabajo en cadena)

La división completa está en [`docs/division_avances_resultados.md`](docs/division_avances_resultados.md). Cada persona trabaja en su sección del mismo notebook, una después de la otra.

| Orden | Persona | Sección del notebook | Estado |
| --- | --- | --- | --- |
| 1 | Persona 1 | 2. Pipeline de datos | Terminada |
| 2 | Persona 2 | 3. Entrenamiento de los modelos | Implementación lista y verificada; ejecución completa pendiente |
| 3 | Persona 3 | 4. Evaluación, comparación y visualizaciones | Pendiente |

### Reglas para trabajar en el mismo notebook

- Antes de empezar: `git pull` y `uv sync`.
- **No cambies `data/splits.csv`**. Todos deben entrenar y evaluar con las mismas imágenes en cada conjunto.
- Si necesitas cambiar algo del preprocesamiento, hazlo en `src/preprocess.py`, no copiando código al notebook, para que la app use exactamente lo mismo.
- Al terminar tu parte: corre el notebook completo, guarda y haz commit con las salidas (gráficas incluidas).
- No subas imágenes, la caché ni los pesos de los modelos (`.pth`); pesan demasiado para GitHub. Los pesos se comparten por Google Drive.
- No tengas el notebook abierto en Jupyter mientras otra herramienta lo edita: Jupyter lo guarda solo y puede sobrescribir los cambios.

### Persona 2: estado y ejecución

La infraestructura y la sección 3 están implementadas y verificadas con pruebas rápidas y offline. Todavía no se ejecutó el entrenamiento completo: no existen checkpoints, historiales finales ni resultados de Dice que se puedan reportar.

Para realizar esa ejecución de forma consciente:

```bash
uv run jupyter notebook proyecto2-resultados.ipynb
```

Después de ejecutar las secciones 1 y 2, en la sección 3 se deben revisar los hiperparámetros y activar `EJECUTAR_PREPARACION = True` y `EJECUTAR_ENTRENAMIENTO = True`. `PESOS_PREENTRENADOS = True` permite descargar los pesos iniciales; para una ejecución completamente offline debe cambiarse a `False`. Con las banderas predeterminadas en `False`, la sección no crea caché, no descarga pesos y no entrena.

La entrega esperada se escribe en `data/artefactos_entrenamiento/`:

- `checkpoints/<modelo>.pt`: mejor checkpoint por Dice de validación para cada modelo.
- `historial_modelos.csv`: columnas `modelo, epoca, train_loss, train_dice, val_loss, val_dice`.
- `experimentos_modelos.csv`: columnas `modelo, arquitectura_encoder, resolucion, batch, learning_rate, epocas_solicitadas, epocas_ejecutadas, mejor_epoca, mejor_val_dice, checkpoint, estado`.

Todo lo necesario del pipeline está en la sección **2.7 Entrega para la Persona 2** del notebook. En resumen:

```python
loaders = pp.crear_dataloaders(splits, CACHE_DIR, size=pp.IMG_SIZE, batch_size=BATCH_SIZE)

for batch in loaders["train"]:
    imagenes = batch["image"].to(device)   # (8, 3, 768, 768)
    mascaras = batch["mask"].to(device)    # (8, 1, 768, 768), valores 0 y 1
```

- Las librerías de modelos ya están declaradas en `pyproject.toml`; `uv sync` instala las versiones bloqueadas.
- GPU: `device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"` funciona con NVIDIA y con Mac de chip M.
- Si te quedas sin memoria en la GPU, baja `BATCH_SIZE` o usa imágenes de 512 px (`size=512` en `preparar_cache` y `crear_dataloaders`, con otro `CACHE_DIR`).

### Persona 3: cómo empezar

- Necesitas los pesos de los 3 modelos que te comparta la Persona 2 por Drive.
- Evalúa con `loaders["test"]`, que no se usó para entrenar ni para elegir hiperparámetros.
- Cada batch trae `batch["organ"]` para calcular el Dice por órgano.
