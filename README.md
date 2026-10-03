# Proyecto 2 – Data Science

**Reto 18: Hackeando el cuerpo humano**. [HuBMAP - Hacking the Human Body](https://www.kaggle.com/competitions/hubmap-organ-segmentation) (Visión Artificial: segmentación de unidades funcionales de tejido, FTU, en imágenes histológicas de riñón, próstata, intestino grueso, bazo y pulmón).

Usamos los datos de la competencia de Kaggle, pero no participamos en ella: no se suben predicciones. Todo se corre en local.

## Estructura

```
proyecto2-reto18.ipynb       Fase 1: análisis exploratorio (entregado)
proyecto2-resultados.ipynb   Fase 2: preprocesamiento, modelos y evaluación
src/preprocess.py            Pipeline de datos compartido (notebook y, después, la app)
src/models.py                Fábricas de los 3 modelos
src/training.py              Loop de entrenamiento, pérdida y preflight de memoria
scripts/windows_training.ps1 Arnés de entrenamiento (Verify / Preflight / Train)
data/
  train.csv                  Se descarga de Kaggle (no se sube al repo)
  train_images/              Se descarga de Kaggle (no se sube al repo)
  splits.csv                 División train/val/test (SÍ se sube: todos usan la misma)
  cache_384/                 Imágenes y máscaras a 384 px (no se sube; va por Drive)
  artefactos_entrenamiento/
    checkpoints/*.pt         Los 3 modelos entrenados (no se suben; van por Drive)
    historial_modelos.csv    Métricas por época (SÍ se sube)
    experimentos_modelos.csv Configuración y mejor Dice por modelo (SÍ se sube)
docs/
  division_avances_resultados.md     Qué hace cada persona en esta fase
  ejecucion_entrenamiento_windows.md Cómo se ejecuta el entrenamiento
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

> **Si eres la Persona 3, sáltate este paso**: no necesitas los 5.8 GB. Ve directo a [Qué sigue: Persona 3](#qué-sigue-persona-3).

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
| 3 | Persona 3 | 4. Evaluación, comparación y visualizaciones | En curso |

### Dónde se quedó (2026-10-02)

La sección 4 se está armando en cuatro partes, una por commit:

| # | Qué | Archivos | Estado |
| --- | --- | --- | --- |
| 1 | Módulo de métricas de prueba | `src/evaluation.py` | Hecho |
| 2 | Correr los 3 modelos sobre `test` | `data/metrics.csv`, `.gitignore` | Hecho |
| 3 | Las visualizaciones | `informe/figuras/`, `informe/figuras_resultados.py` | Pendiente |
| 4 | Escribir la sección 4 del notebook | `proyecto2-resultados.ipynb` | Pendiente |

La discusión final (4.4) la escribe la Persona 3, para que quede como su contribución.

Pendiente aparte: subir al Drive `data/artefactos_entrenamiento/checkpoints/`, `data/cache_384/` y `data/train.csv` (312 MB) y pasarle el link a la Persona 3.

### Reglas para trabajar en el mismo notebook

- Antes de empezar: `git pull` y `uv sync`.
- **No cambies `data/splits.csv`**. Todos deben entrenar y evaluar con las mismas imágenes en cada conjunto.
- Si necesitas cambiar algo del preprocesamiento, hazlo en `src/preprocess.py`, no copiando código al notebook, para que la app use exactamente lo mismo.
- Al terminar tu parte: corre el notebook completo, guarda y haz commit con las salidas (gráficas incluidas).
- No subas imágenes, la caché ni los pesos de los modelos (`.pt`); pesan demasiado para GitHub y se comparten por Google Drive. Los dos CSV del entrenamiento sí están versionados: pesan 11 KB juntos.
- No tengas el notebook abierto en Jupyter mientras otra herramienta lo edita: Jupyter lo guarda solo y puede sobrescribir los cambios.

### Persona 2: entrenamiento (terminado)

Ejecutado el **2026-10-01** en una RTX 4060 Laptop de 8 GB con el arnés de PowerShell. Resultados reales:

| Modelo | Épocas | Mejor época | Mejor val Dice | Estado |
| --- | --- | --- | --- | --- |
| SegFormer / MIT-B0 | 10 | 5 | **0.6596** | detención temprana |
| U-Net / ResNet34 | 13 | 8 | 0.6058 | detención temprana |
| U-Net++ / ResNet34 | 6 | 1 | 0.5256 | detención temprana |

**El valor de U-Net++ subestima al modelo**: su mejor época fue la 1 y su `train_dice` seguía subiendo (0.37 → 0.67), así que lo cortó el ruido de validación (53 imágenes de validación y batch efectivo 2), no una falta de aprendizaje. Hay que decirlo en la discusión en lugar de presentar 0.5256 como su techo. Como referencia, los tres primeros lugares del reto llegaron a Dice ≈ 0.835, con resoluciones mayores, ensambles y pseudo-etiquetado.

Perfil usado, elegido para que el flujo completo quepa en una GPU portátil de 6 a 8 GB:

- resolución **384 × 384 px**;
- batch físico **1 imagen** (lo que reside en la GPU en cada forward/backward);
- acumulación de gradientes de **2 pasos** → batch efectivo de **2 imágenes**;
- precisión mixta (AMP) con CUDA.

Artefactos en `data/artefactos_entrenamiento/`:

- `checkpoints/<modelo>.pt`: mejor checkpoint por Dice de validación, uno por modelo (no se versiona, va por Drive).
- `historial_modelos.csv`: `modelo, epoca, train_loss, train_dice, val_loss, val_dice`. **Sí está en el repo.**
- `experimentos_modelos.csv`: configuración, épocas ejecutadas, mejor época, mejor val Dice, checkpoint y estado. **Sí está en el repo.**

**Para repetir el entrenamiento**, si alguna vez hace falta: el único camino autorizado es el arnés descrito en [`docs/ejecucion_entrenamiento_windows.md`](docs/ejecucion_entrenamiento_windows.md), con la secuencia de `comandos_windows.txt`. Exige CUDA en Windows nativo y valida datos, GPU y memoria antes de gastar tiempo. No se entrena desde el notebook ni se editan sus banderas; el contrato del pipeline está en la sección **2.7 Entrega para la Persona 2**.

## Qué sigue: Persona 3

Evaluación en el conjunto de prueba, comparación y visualizaciones. Es la **sección 4** del notebook, que hoy está vacía.

**No necesitas GPU ni descargar las imágenes.** Son 53 imágenes a 384 px por modelo: la inferencia corre en CPU en minutos.

### Lo que ya viene en el repositorio

Con `git pull` y `uv sync` ya tienes:

| Archivo | Para qué |
| --- | --- |
| `data/splits.csv` | la misma partición con la que se entrenó |
| `data/artefactos_entrenamiento/historial_modelos.csv` | curvas de pérdida y Dice por época, una de las visualizaciones pedidas |
| `data/artefactos_entrenamiento/experimentos_modelos.csv` | configuración y mejor val Dice por modelo |

### Lo que tienes que bajar del Drive (312 MB)

Los pesos y la caché no caben en GitHub. Copia esto dentro de `data/`:

| Carpeta o archivo | Tamaño | Para qué |
| --- | --- | --- |
| `artefactos_entrenamiento/checkpoints/` (3 `.pt`) | 208 MB | los modelos entrenados |
| `cache_384/` (702 `.png`) | 89 MB | imágenes y máscaras a 384 px; te evita los 5.8 GB de `.tiff` |
| `train.csv` | 16 MB | órgano, `pixel_size` y tamaños originales |

### Cómo correrlo

1. `git pull` y `uv sync`.
2. Copia los archivos del Drive dentro de `data/`.
3. `uv run jupyter notebook proyecto2-resultados.ipynb` y ejecuta la *Configuración inicial* y **toda la sección 2**. Debe imprimir `caché de 384 px: True`, `Archivos en la caché: 702` y `test : 53 imágenes`.
4. **No ejecutes la sección 3.** Sus banderas están en `False` a propósito: no entrena nada, solo imprime "omitido".
5. Escribe tu sección 4.

### Lo que necesitas saber para la sección 4

- Evalúa con `loaders["test"]`, que no se usó para entrenar ni para elegir hiperparámetros. Cada batch trae `batch["organ"]` para el Dice por órgano.
- Carga cada checkpoint así; el `.pt` guarda solo el `state_dict` (ejemplo completo en la sección **3.5** del notebook):

```python
estado = torch.load(f"data/artefactos_entrenamiento/checkpoints/{nombre}.pt", map_location="cpu")
modelo = crear_modelo(nombre, pesos_preentrenados=False)
modelo.load_state_dict(estado["modelo"])
modelo.eval()
```

- **SegFormer devuelve `(batch, 1, 96, 96)`**, un cuarto de la entrada: hay que interpolarlo a `(384, 384)` antes de compararlo con la máscara. U-Net y U-Net++ ya devuelven `(batch, 1, 384, 384)`.
- Los checkpoints son de 384 px: evalúa a esa resolución o las métricas no serán comparables.
- Si mides **tiempo de inferencia** en CPU, dilo en el informe junto con el hardware.

**Entregables:** `metrics.csv` (por imagen y por modelo), al menos 3 visualizaciones estáticas en `informe/figuras/` y la discusión con el modelo seleccionado.
