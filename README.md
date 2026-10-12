# Proyecto 2 – Data Science: resultados y demo

**Reto 18: Hackeando el cuerpo humano.** Segmentación binaria de unidades
funcionales de tejido (FTU), no clasificación de órganos. Datos de
[HuBMAP – Hacking the Human Body](https://www.kaggle.com/competitions/hubmap-organ-segmentation);
no participamos en la competencia ni enviamos predicciones. Prototipo de
investigación, **no apto para diagnóstico ni decisiones médicas**.

SegFormer / MIT-B0 es la referencia de esta ejecución: Dice medio **0.629** e
IoU **0.510** sobre 53 imágenes. La aplicación explora metadatos y resultados
existentes; la predicción de imágenes nuevas está implementada, pero **los pesos
no están disponibles en este checkout y la aceptación real sigue pendiente**.

## Inicio rápido: aplicación local

Desde la raíz del repositorio, con `uv` y Python 3.11 o posterior:

```bash
uv sync --frozen
uv run streamlit run app/Inicio.py
```

Abra `http://localhost:8501` (o la dirección que indique Streamlit); cierre con
`Ctrl + C`. No necesita GPU para la aplicación. Repita la sincronización si cambia
el lock o las dependencias. Instalar paquetes no recupera datos ni checkpoints.

- **macOS Apple Silicon:** el lock incluye wheels arm64 para macOS 14 o posterior;
  Torch usa PyPI y los modelos se cargan en CPU, aunque MPS esté disponible.
  El Python 3.9 del sistema no cumple el requisito.
- **Windows:** se conserva Torch `2.14.1+cu130` desde el índice CUDA cu130 y
  torchvision `0.29.1` desde PyPI. Instalar la app no valida CUDA ni autoriza
  entrenamiento. Consulte el [contrato Windows](docs/ejecucion_entrenamiento_windows.md).

## Demo sin pesos: lo que sí se puede mostrar

1. **Inicio:** resumen de modelos y avisos de activos faltantes.
2. **Exploración:** distribución de órganos/splits y filtros. Sin `train.csv`,
   no se muestran edad, fuente, dimensiones ni cobertura como si estuvieran disponibles.
3. **Rendimiento:** seleccione un modelo o todos, órganos y Dice/IoU; muestre
   comparación, distribución, tiempos y curvas. Desactive **Mostrar rendimiento**
   y vuelva a Inicio: resumen y resultados permanecen ocultos hasta reactivarlo.
4. **Predicción:** muestre el aviso de bloqueo por checkpoints ausentes.
   No simule una predicción ni presente pruebas sintéticas como demo con pesos reales.

Con pesos recuperados de origen confiable, Predicción acepta PNG/JPEG/TIFF de una
sola imagen (hasta 64 MiB y 9 millones de píxeles), preprocesa a 384 px y permite
uno/todos los modelos disponibles. Devuelve máscara FTU, superposición cian,
porcentaje FTU y tiempo CPU; no Dice/IoU sin anotación de referencia. El órgano
seleccionado es descriptivo. Si no se conoce el espaciado, se asume explícitamente
0.4 µm/píxel. La recuperación y comprobación real de este flujo son pendientes.

## Activos y resultados reproducibles

| Ruta | Uso y estado local |
| --- | --- |
| `data/splits.csv` | Versionado: 351 IDs, split 245/53/53, estratificado por órgano, semilla 42 |
| `data/metrics.csv` | Versionado: 159 filas, tres modelos sobre las mismas 53 imágenes |
| `data/artefactos_entrenamiento/historial_modelos.csv` | Curvas de entrenamiento/validación existentes |
| `data/artefactos_entrenamiento/experimentos_modelos.csv` | Perfil, mejor época y estado existentes |
| `data/train.csv` | Metadatos completos/RLE; ausente localmente, para EDA enriquecido |
| `data/cache_384/` | Caché de 351 imágenes y 351 máscaras; ausente, no necesaria para la demo de CSV ni una carga nueva |
| `data/artefactos_entrenamiento/checkpoints/` | Pesos ausentes: `unet_resnet34.pt`, `unetplusplus_resnet34.pt`, `segformer_mit_b0.pt` |

Pesos, caché, TIFF y `train.csv` están excluidos de Git: no forzar su inclusión.
Coordine la entrega de activos existentes por un canal autorizado; no hay enlace
Drive confirmado en este README. Descarga original de metadatos:
[datos de Kaggle](https://www.kaggle.com/competitions/hubmap-organ-segmentation/data),
sujeta a las reglas de acceso de la competencia. No hace falta descargar los TIFF
para mostrar los resultados guardados ni para inferir una carga nueva con pesos.

| Modelo | Dice prueba | IoU prueba | Forward registrado (ms) | Mejor val Dice | Épocas / mejor época |
| --- | --- | --- | --- | --- | --- |
| U-Net / ResNet34 | 0.506 | 0.400 | 11.8 | 0.6058 | 13 / 8 |
| U-Net++ / ResNet34 | 0.481 | 0.355 | 31.9 | 0.5256 | 6 / 1 |
| SegFormer / MIT-B0 | **0.629** | **0.510** | 11.6 | **0.6596** | 10 / 5 |

Medias por imagen de los CSV existentes, no métricas globales de píxeles. Tiempos
del forward en **NVIDIA GeForce RTX 4060 Laptop GPU**, batch 1, sin carga ni
preprocesamiento: **no son un benchmark de este Mac**. Los tres modelos terminaron
por detención temprana. No hay réplicas ni intervalos de confianza; el resultado
de U-Net++ no demuestra su techo ni una causa específica de detención.

El perfil conservador usa 384 × 384 px, batch físico 1, acumulación de gradientes 2, AMP CUDA,
AdamW (LR 1e-4, weight decay 1e-2), Dice + BCE, máximo 20 épocas y paciencia 5.
Checkpoint por validación, umbral fijo ≥ 0.5; no ajustar usando prueba.
Split por imagen no prueba independencia por donante ni transferencia HPA/HuBMAP.
Los artefactos conservan `checkpoints/<modelo>.pt`,
`historial_modelos.csv` (`modelo, epoca, train_loss, train_dice, val_loss, val_dice`)
y `experimentos_modelos.csv` (configuración, épocas, mejor época/Dice, checkpoint y estado).
El contrato de referencia del notebook es **2.7 Entrega para la Persona 2**;
no se ejecuta para preparar esta entrega.

## Comprobaciones funcionales y presentación

Suite sintética/offline (no evaluación de imágenes reales ni entrenamiento):

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 ALBUMENTATIONS_NO_VERSION_CHECK=1 UV_OFFLINE=1 UV_FROZEN=1 uv run python -m unittest discover -s tests -v
git diff --check
```

La sintaxis de variables es para una shell POSIX. Los contratos Windows son
sintéticos; no equivalen a Verify/Preflight en Windows nativo. TDD no está
configurado; estos son controles funcionales, no una afirmación de TDD.

Presentación: `presentacion/presentacion.tex` y `presentacion/presentacion.pdf`.
**Estado de este checkout:** PDF de resultados actualizado (20 páginas), compilado
con pdfLaTeX sin shell escape. Metropolis y `pgfopts` se instalaron exclusivamente
en el árbol TeX del usuario desde el repositorio oficial CTAN; no se cambió el tema
ni se instalaron herramientas de sistema. La aceptación con pesos reales sigue pendiente.
Con pdfLaTeX y el tema Metropolis ya instalados, desde `presentacion/`, ejecute
dos veces para resolver citas y numeración:

```bash
pdflatex -no-shell-escape -interaction=nonstopmode -halt-on-error presentacion.tex
pdflatex -no-shell-escape -interaction=nonstopmode -halt-on-error presentacion.tex
```

Reutiliza tres figuras `informe/figuras/resultados_*.png` y fuentes de la
bibliografía existente. **No regenere las figuras:** el script de figuras incluye
inferencia sobre prueba. Los notebooks son referencias; no ejecutar Run All para
preparar la demo. El entrenamiento solo sigue el arnés Windows documentado,
con gates y confirmación humana; no invocar directamente el runner Python.

## Checklist antes de entregar

- [ ] Abrir la app y recorrer las cuatro páginas; comprobar filtros y ocultamiento.
- [ ] Recuperar los tres checkpoints confiables y `train.csv`; caché si se requiere.
- [ ] Comprobar una imagen nueva autorizada con uno/todos los modelos disponibles;
      no usar el split de prueba para iterar la demo. Capturar pantallas reales.
- [ ] Revisar el PDF compilado: cifras, figuras, citas, legibilidad y sin desbordes.
- [ ] Completar/verificar el informe final por separado y las capturas solicitadas;
      esta actualización no modifica ni acredita el informe.
- [ ] Confirmar el enlace humano de Drive y sus permisos; entregar PDF, código,
      repositorio y presentación según [la guía](docs/instrucciones_entrega_final.md).
- [ ] Auditar APA/indexación de las referencias cuando corresponda; no se certificó aquí.

Código: `app/` (cuatro páginas), `src/inference.py` (cargas nuevas),
`src/preprocess.py`, `src/models.py`, `src/training.py`, `src/evaluation.py`.
Historial de aceptación y límites: [tracking local](odd/tasks/final-delivery-completion.md).
