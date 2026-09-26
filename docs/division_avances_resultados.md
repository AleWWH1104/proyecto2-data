# División de trabajo: Avances de Resultados

**Reto 18: Hackeando el cuerpo humano** ([HuBMAP - Hacking the Human Body](https://www.kaggle.com/competitions/hubmap-organ-segmentation))

Este avance cubre la parte práctica: preprocesamiento, entrenamiento y evaluación de los modelos (actividades 3 a 6 de la guía). La investigación y la selección de modelos (actividades 1 y 2) ya están hechas, en la sección 1 de `proyecto2-resultados.ipynb`. La aplicación queda para la siguiente fase.

El trabajo es **en cadena**: cada persona empieza cuando la anterior le entrega lo que se indica en "Entrega". Todo se trabaja en el mismo notebook, `proyecto2-resultados.ipynb`, cada quien en su sección. Cada persona sube su trabajo con sus propios commits a GitHub, porque se evalúan las contribuciones individuales.

## Resumen

| Orden | Persona   | Tema                                      |
| ----- | --------- | ----------------------------------------- |
| 1     | Persona 1 | Pipeline de datos                         |
| 2     | Persona 2 | Entrenamiento de los modelos              |
| 3     | Persona 3 | Evaluación, comparación y visualizaciones |

Modelos seleccionados en la investigación: **U-Net** con encoder ResNet34 (baseline), **U-Net++** y **SegFormer**.

## Persona 1: Pipeline de datos

**Qué hace**

- Decodificar las máscaras RLE de `train.csv` a máscaras binarias.
- Redimensionar las imágenes de ~3000×3000 px a un tamaño entrenable (por ejemplo 512 o 768 px) y ajustar el tamaño de píxel entre las fuentes HPA y HuBMAP.
- Normalizar la tinción o aplicar augmentation de color, y definir el data augmentation (flips, rotaciones, brillo y contraste).
- Dividir los datos en entrenamiento, validación y prueba **estratificados por órgano**, porque hay órganos con muy pocas imágenes.
- Crear la clase `Dataset` y los `DataLoader` de PyTorch.
- Verificar visualmente el pipeline: imagen con su máscara superpuesta para cada órgano.
- Dejar el preprocesamiento en un módulo reutilizable (`src/preprocess.py`) para que después lo use la aplicación.

**Entrega**

- `src/preprocess.py` funcionando.
- `data/splits.csv` con el id de cada imagen y el conjunto al que pertenece.
- Los `DataLoader` funcionando.

## Persona 2: Entrenamiento de los modelos

**Qué hace**

- Escribir un loop de entrenamiento común para los 3 modelos: pérdida Dice + BCE, early stopping y guardado del mejor checkpoint según el Dice de validación.
- Entrenar U-Net (baseline), U-Net++ y SegFormer en local con GPU (`segmentation_models_pytorch` para U-Net y U-Net++, `transformers` para SegFormer).
- Ajustar hiperparámetros: learning rate, tamaño de imagen y encoder. Registrar cada experimento.

**Entrega**

- Pesos de los 3 modelos (`.pth`).
- Historial de pérdida y Dice por época de cada modelo (por ejemplo `historial.csv`).
- Tabla de experimentos: qué hiperparámetros se probaron y qué Dice de validación dio cada uno.

## Persona 3: Evaluación, comparación y visualizaciones

**Qué hace**

- Evaluar los 3 modelos en el conjunto de prueba: Dice, IoU, Dice por órgano y tiempo de inferencia.
- Guardar los resultados en `metrics.csv` (por imagen y por modelo), que después usará la aplicación.
- Generar al menos 3 visualizaciones estáticas con colores adecuados:
    1. Comparación de Dice e IoU por modelo.
    2. Dice por órgano para cada modelo.
    3. Curvas de pérdida y Dice de entrenamiento y validación.
    4. Ejemplos de imagen original, máscara real y predicción de cada modelo.
- Discutir los resultados y seleccionar el mejor modelo, relacionándolo con los hallazgos del análisis exploratorio (por ejemplo, órganos con FTU pequeñas o con pocas imágenes).

**Entrega**

- `metrics.csv` y las figuras en `informe/figuras/`.
- Discusión de resultados y modelo seleccionado.

## Cosas que hay que acordar antes de empezar

- **Formato de `splits.csv`, `historial.csv` y `metrics.csv`**: definirlo desde el inicio para que cada persona reciba lo que espera.
- **Datos**: cada persona descarga una vez `train_images/` en `data/` (ver el README). Las imágenes y la caché no se suben al repositorio.
- **Pasar el turno**: antes de pasarle el turno a la siguiente persona, subir el notebook ejecutado al repositorio. Los pesos de los modelos pesan mucho para GitHub; compártanlos por Google Drive.
