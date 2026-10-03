# División de trabajo: Aplicación

**Reto 18: Hackeando el cuerpo humano** ([HuBMAP - Hacking the Human Body](https://www.kaggle.com/competitions/hubmap-organ-segmentation))

Los modelos ya están entrenados y evaluados (secciones 1 a 4 de `proyecto2-resultados.ipynb`). Esta fase construye la aplicación que pide la guía. **No hay que volver a ejecutar el notebook ni entrenar nada**: todo lo que la app necesita ya está en el repositorio o en el Drive.

## Antes de empezar

### 1. Bajar del Drive (312 MB)

Después de `git pull` y `uv sync`, copiar dentro de la carpeta `data/` del repositorio:

| Del Drive                 | Va en                                        | Tamaño | Para qué                                                 |
| ------------------------- | -------------------------------------------- | ------ | -------------------------------------------------------- |
| `checkpoints/` (3 `.pt`)  | `data/artefactos_entrenamiento/checkpoints/` | 208 MB | los modelos, para segmentar imágenes                     |
| `cache_384/` (702 `.png`) | `data/cache_384/`                            | 89 MB  | imágenes y máscaras a 384 px, para los ejemplos          |
| `train.csv`               | `data/train.csv`                             | 16 MB  | variables del dataset (también se puede bajar de Kaggle) |

Debe quedar así:

```
data/
  train.csv
  splits.csv                       (ya está en el repo)
  metrics.csv                      (ya está en el repo)
  cache_384/
  artefactos_entrenamiento/
    historial_modelos.csv          (ya está en el repo)
    experimentos_modelos.csv       (ya está en el repo)
    checkpoints/
      unet_resnet34.pt
      unetplusplus_resnet34.pt
      segformer_mit_b0.pt
```

Ninguno de estos archivos se sube a GitHub; ya están en `.gitignore`.

### 2. Lo que ya existe y se reutiliza

| Qué                                                                                          | Dónde                                                                     |
| -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| Métricas de test por imagen y modelo (`modelo, id, organ, dice, iou, segundos, dispositivo`) | `data/metrics.csv`                                                        |
| Pérdida y Dice por época                                                                     | `data/artefactos_entrenamiento/historial_modelos.csv`                     |
| Configuración y mejor época de cada modelo                                                   | `data/artefactos_entrenamiento/experimentos_modelos.csv`                  |
| Qué imagen es de train, val o test                                                           | `data/splits.csv`                                                         |
| Preprocesamiento de una imagen nueva                                                         | `pp.preprocesar_para_modelo(img, pixel_size)` en `src/preprocess.py`      |
| Regresar la predicción al tamaño original                                                    | `pp.postprocesar(probabilidades, tamano_original)` en `src/preprocess.py` |
| Cargar un modelo entrenado                                                                   | `cargar_modelo_entrenado(nombre, ruta)` en `src/evaluation.py`            |
| Ajustar la salida de SegFormer (96 → 384 px)                                                 | `adaptar_logits(salida, mascaras)` en `src/training.py`                   |
| Colores de cada modelo (U-Net azul, U-Net++ naranja, SegFormer verde)                        | `MODELOS` y `COLORES` en `informe/figuras_resultados.py`                  |

Los modelos corren en CPU: una imagen tarda menos de un segundo. No se necesita GPU.

### 3. Acuerdos

- **Tecnología:** Streamlit para la app y Plotly para las gráficas interactivas. Se agregan con `uv add streamlit plotly` (lo hace la Persona 1 en el esqueleto).
- **Estructura:** una página por persona, para no editar los mismos archivos.

```
app/
  Inicio.py              Persona 1: portada y navegación
  comun.py               Persona 1: carga de datos y modelos con caché
  pages/
    1_Exploracion.py     Persona 3
    2_Prediccion.py      Persona 2
    3_Rendimiento.py     Persona 3
```

- Se corre con `uv run streamlit run app/Inicio.py`.
- **Colores:** los mismos de las figuras del informe para cada modelo, y cian (`#00e5ff`) para las máscaras sobre la imagen. Así la app y el informe se ven como un solo trabajo.
- **Modelo por defecto:** SegFormer / MIT-B0, el seleccionado en la sección 4.4.

## Resumen

| Persona   | Qué hace                                              | Requisito de la guía                                                                          | Puntos de la rúbrica                                                      |
| --------- | ----------------------------------------------------- | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| Persona 1 | Esqueleto de la app (portada y funciones compartidas) | diseño intuitivo, base para las demás páginas                                                 | —                                                                         |
| Persona 2 | Predicción sobre imágenes nuevas                      | ingresar datos nuevos; ver cada modelo o todos                                                | "Preprocesamiento de la entrada" (15) y "Presentación de resultados" (20) |
| Persona 3 | Exploración de los datos y rendimiento de los modelos | (a) explorar las variables y (c) gráficas interactivas del rendimiento que se puedan esconder | "Presentación de resultados" (20) y "Eficiencia de los modelos" (15)      |

## Persona 1: Esqueleto de la app

Va primero, porque desbloquea a los demás.

- `uv add streamlit plotly` y subir `pyproject.toml` y `uv.lock`.
- `app/Inicio.py`: título, descripción corta del reto, el modelo seleccionado y qué hace cada página.
- `app/comun.py` con funciones cacheadas que usan las otras páginas:
    - `cargar_datos()`: lee `train.csv`, `splits.csv`, `metrics.csv` e `historial_modelos.csv` (`@st.cache_data`).
    - `cargar_modelo(nombre)`: usa `cargar_modelo_entrenado` en CPU (`@st.cache_resource`, para cargarlo una sola vez).
    - Los nombres y colores de los modelos, importados de `informe/figuras_resultados.py`.

**Entrega:** `app/Inicio.py` y `app/comun.py`, y que `uv run streamlit run app/Inicio.py` abra la app.

## Persona 2: Predicción sobre imágenes nuevas

- Subir una imagen (`.tiff` o `.png`) o elegir una de las 53 de test de `cache_384/`, filtrando por órgano.
- El preprocesamiento debe pasar inadvertido para el usuario: `preprocesar_para_modelo` y `postprocesar` hacen todo. Para un `.tiff` se lee con `pp.leer_imagen`.
- Elegir un modelo o los tres. Mostrar la imagen con la máscara predicha superpuesta, una columna por modelo.
- Para cada modelo mostrar el porcentaje de la imagen cubierto por FTU y el tiempo de inferencia.
- Si la imagen es de test, mostrar también la máscara real y el Dice de cada modelo (de `metrics.csv`), para comparar las respuestas.

**Entrega:** `app/pages/2_Prediccion.py`.

## Persona 3: Exploración de los datos y rendimiento de los modelos

Las dos páginas son gráficas interactivas a partir de CSV, sin correr modelos.

**Página de exploración** (`app/pages/1_Exploracion.py`)

- Filtros por órgano, fuente (HPA o HuBMAP) y sexo.
- Gráficas de las variables usadas por los modelos: distribución por órgano, edad, tamaño de imagen, `pixel_size` y proporción de FTU (se calcula del RLE con `pp.rle_decode`, o sumando las longitudes del RLE como en `informe/figuras.py`).
- Contar los hallazgos del análisis exploratorio que explican los resultados: el pulmón tiene la menor proporción de FTU y pocas imágenes, y por eso es el peor órgano para los tres modelos.

**Página de rendimiento** (`app/pages/3_Rendimiento.py`)

- Gráficas con tooltip a partir de `metrics.csv` y del historial: Dice e IoU por modelo, Dice por órgano, distribución del Dice por imagen (box o violín) y curvas de entrenamiento y validación por época.
- Tiempo de inferencia por modelo, aclarando que se midió en una RTX 4060 Laptop.
- Filtros por modelo y por órgano.
- Cada gráfica dentro de un `st.expander` o con un toggle, para que el usuario pueda esconderla (lo pide la guía).
- Un resumen de la discusión de la sección 4.4: por qué SegFormer, por qué falla el pulmón y la limitación de U-Net++.

**Entrega:** `app/pages/1_Exploracion.py` y `app/pages/3_Rendimiento.py`.

## Al terminar

Las personas 2 y 3 mandan una captura de pantalla de cada una de sus páginas para la sección de la aplicación del informe.
