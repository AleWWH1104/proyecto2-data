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
  cache_384/                 Imágenes y máscaras a 384 px (no se sube al repo; se comparte por Drive)
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

El notebook del análisis exploratorio solo necesita `train.csv`.

**Los `.tiff` solo se necesitan para generar la caché.** La sección 2.2 crea una vez `data/cache_384/` (702 `.png`: 351 imágenes y 351 máscaras ya redimensionadas) y a partir de ahí todo —entrenamiento, evaluación y la app— lee de ahí. Quien reciba `data/cache_384/` por Drive puede trabajar **sin descargar los 5.8 GB**: es el caso de la Persona 3.

### 3. Abrir el notebook

```bash
uv run jupyter notebook proyecto2-resultados.ipynb
```

Corre todas las celdas desde el inicio (Run All). La primera celda imprime dos banderas:

- `TIFF originales: True` → se puede generar la caché.
- `caché de 384 px: True` → la sección 2 completa y la sección 4 funcionan, haya `.tiff` o no.

Si ambas son `False`, falta descargar `train_images/` o pedir `data/cache_384/`. Generar la caché tarda unos minutos y solo se hace una vez.

**La sección 3 no se ejecuta desde el notebook.** Sus banderas quedan en `False` a propósito; el entrenamiento va por el arnés de PowerShell (ver más abajo).

## Fase 2: Resultados (trabajo en cadena)

La división completa está en [`docs/division_avances_resultados.md`](docs/division_avances_resultados.md). Cada persona trabaja en su sección del mismo notebook, una después de la otra.

| Orden | Persona | Sección del notebook | Estado |
| --- | --- | --- | --- |
| 1 | Persona 1 | 2. Pipeline de datos | Terminada |
| 2 | Persona 2 | 3. Entrenamiento de los modelos | Terminada: los tres modelos entrenados y sus artefactos generados |
| 3 | Persona 3 | 4. Evaluación, comparación y visualizaciones | Pendiente |

### Reglas para trabajar en el mismo notebook

- Antes de empezar: `git pull` y `uv sync`.
- **No cambies `data/splits.csv`**. Todos deben entrenar y evaluar con las mismas imágenes en cada conjunto.
- Si necesitas cambiar algo del preprocesamiento, hazlo en `src/preprocess.py`, no copiando código al notebook, para que la app use exactamente lo mismo.
- Al terminar tu parte: corre el notebook completo, guarda y haz commit con las salidas (gráficas incluidas).
- No subas imágenes, la caché ni los pesos de los modelos (`.pth`); pesan demasiado para GitHub. Los pesos se comparten por Google Drive.
- No tengas el notebook abierto en Jupyter mientras otra herramienta lo edita: Jupyter lo guarda solo y puede sobrescribir los cambios.

### Persona 2: estado y ejecución

El entrenamiento completo se ejecutó el **2026-10-01** en una RTX 4060 Laptop de 8 GB, por el arnés de PowerShell, y dejó los tres checkpoints y los dos CSV en `data/artefactos_entrenamiento/`. Mejor Dice de validación por modelo:

| Modelo | Épocas ejecutadas | Mejor época | Mejor val Dice | Estado |
| --- | --- | --- | --- | --- |
| SegFormer / MIT-B0 | 10 | 5 | **0.6596** | detención temprana |
| U-Net / ResNet34 | 13 | 8 | 0.6058 | detención temprana |
| U-Net++ / ResNet34 | 6 | 1 | 0.5256 | detención temprana |

Los tres pararon por early stopping (paciencia 5). **El valor de U-Net++ subestima al modelo**: su mejor época fue la 1 y su `train_dice` seguía subiendo (0.37 → 0.67), así que lo cortó el ruido de validación (53 imágenes de validación y batch efectivo 2), no una falta de aprendizaje. Conviene decirlo en la discusión en lugar de presentar 0.5256 como su techo.

Como referencia, los tres primeros lugares del reto obtuvieron Dice ≈ 0.835 en el test privado, con resoluciones mayores, ensambles y pseudo-etiquetado; aquí se entrenó un solo modelo por arquitectura a 384 px con batch efectivo 2.

El camino autorizado para la ejecución final es el arnés de PowerShell descrito en [`docs/ejecucion_entrenamiento_windows.md`](docs/ejecucion_entrenamiento_windows.md); `comandos_windows.txt` contiene la secuencia para la operadora. El notebook conserva la configuración y el contexto como referencia, pero no se usa para iniciar el entrenamiento final ni se editan sus banderas.

El perfil predeterminado prioriza completar el flujo en una **NVIDIA GeForce RTX 4050 Laptop de 6 GB** y también es aplicable a una RTX 4060 Laptop de 8 GB:

- resolución: **384 × 384 px**;
- batch físico: **1 imagen**, que es lo que reside en la GPU durante cada forward/backward;
- acumulación de gradientes: **2 pasos**;
- batch efectivo: **2 imágenes** (`1 × 2`) antes de cada actualización del optimizador;
- precisión mixta (AMP) cuando el dispositivo es CUDA.

Antes del entrenamiento completo, el arnés ejecuta un preflight separado para U-Net, U-Net++ y SegFormer. Cada prueba realiza forward, adaptación de logits, pérdida Dice + BCE, backward y un paso AdamW para materializar su estado; además informa los picos de memoria CUDA asignada y reservada. La memoria se limpia entre modelos y un OOM detiene el flujo antes de iniciar el entrenamiento. Que el preflight termine no garantiza disponibilidad posterior si otros procesos comienzan a consumir GPU.

La entrega esperada se escribe en `data/artefactos_entrenamiento/`:

- `checkpoints/<modelo>.pt`: mejor checkpoint por Dice de validación para cada modelo.
- `historial_modelos.csv`: columnas `modelo, epoca, train_loss, train_dice, val_loss, val_dice`.
- `experimentos_modelos.csv`: columnas `modelo, arquitectura_encoder, resolucion, batch, acumulacion_gradientes, batch_efectivo, learning_rate, epocas_solicitadas, epocas_ejecutadas, mejor_epoca, mejor_val_dice, checkpoint, estado`. `batch` conserva el significado de batch físico.

Todo lo necesario del pipeline está en la sección **2.7 Entrega para la Persona 2** del notebook. En resumen:

```python
loaders = pp.crear_dataloaders(splits, CACHE_DIR, size=pp.IMG_SIZE, batch_size=BATCH_SIZE)

for batch in loaders["train"]:
    imagenes = batch["image"].to(device)   # (8, 3, 384, 384)
    mascaras = batch["mask"].to(device)    # (8, 1, 384, 384), valores 0 y 1
```

- Las librerías de modelos ya están declaradas en `pyproject.toml`; `uv sync --frozen` instala las versiones bloqueadas.
- El perfil operativo exige CUDA en Windows nativo y conserva el split `test` exclusivamente para Persona 3.
- Si el preflight falla por memoria con batch físico 1, cierre otros procesos que usen la GPU y repita desde `Verify`; no cambie el perfil conservador durante el handoff.

### Persona 3: cómo empezar

**No necesitas descargar las imágenes ni tener GPU.** La inferencia son 53 imágenes a 384 px por modelo: corre en CPU en minutos.

1. `git pull` y `uv sync`.
2. Copia de la carpeta de Drive que comparte la Persona 2, dentro de `data/`:

```
data/
  splits.csv                     ya está en el repositorio
  train.csv                      16 MB
  cache_384/                     702 .png (351 imágenes y 351 máscaras)
  artefactos_entrenamiento/
    checkpoints/unet_resnet34.pt
    checkpoints/unetplusplus_resnet34.pt
    checkpoints/segformer_mit_b0.pt
    historial_modelos.csv
    experimentos_modelos.csv
```

3. Ejecuta la *Configuración inicial* y **toda la sección 2**. Debe imprimir `caché de 384 px: True` y `test : 53 imágenes`. No ejecutes la sección 3: sus banderas están en `False` a propósito.
4. Evalúa con `loaders["test"]`, que no se usó para entrenar ni para elegir hiperparámetros. Cada batch trae `batch["organ"]` para el Dice por órgano.
5. Carga cada checkpoint con `crear_modelo(nombre, pesos_preentrenados=False)` y `modelo.load_state_dict(estado["modelo"])`; el `.pt` guarda solo el `state_dict`. El ejemplo completo está en la sección **3.5** del notebook.

Los checkpoints son de 384 px: evalúa a esa resolución o las métricas no serán comparables. Si mides **tiempo de inferencia** en CPU, dilo en el informe junto con el hardware.
