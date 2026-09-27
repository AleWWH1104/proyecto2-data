# Persona 2: entrenamiento de modelos

## Objetivo

Completar la sección 3 de `proyecto2-resultados.ipynb` con un flujo reproducible para entrenar U-Net, U-Net++ y SegFormer, registrar sus experimentos y entregar artefactos compatibles con la evaluación de la Persona 3.

## Problema y motivación

La sección asignada a la Persona 2 está vacía. El repositorio ya contiene las 351 imágenes y una división estratificada, pero no tiene caché procesada, dependencias de modelos, checkpoints, historiales ni tabla de experimentos. La máquina disponible no tiene CUDA ni MPS, por lo que la implementación debe poder validarse con pruebas cortas en CPU sin pretender completar entrenamientos de larga duración.

## Alcance autorizado

- Implementar la infraestructura común de entrenamiento con pérdida Dice + BCE, validación, early stopping y checkpoints.
- Integrar U-Net ResNet34, U-Net++ ResNet34 y SegFormer MIT-B0.
- Configurar una ejecución local viable a 512 px y batch pequeño.
- Registrar historial y experimentos en formatos reutilizables por la Persona 3.
- Ejecutar pruebas de humo; no ejecutar entrenamientos completos de horas o días.
- No modificar `data/splits.csv`, no versionar pesos ni archivos de caché.

## Restricciones

- Conservar el conjunto `test` exclusivamente para la Persona 3.
- Usar logits de un canal y redimensionar la salida de SegFormer antes de calcular pérdida o métricas.
- Mantener código y documentación en español neutral, coherente con el repositorio.
- TDD no configurado; se aplicarán verificaciones funcionales y pruebas de humo.
- Estrategia de entrega: `ask-on-risk`; al superar la guía de 400 líneas se eligió `stacked-to-main` para futuras PRs.

## Tareas

- [x] **P2-1 — Preparar dependencias y módulo de entrenamiento.** Agregar dependencias reproducibles e implementar pérdida, Dice, adaptación de logits, entrenamiento/validación, early stopping y checkpoints.
- [x] **P2-2 — Integrar los tres modelos y la sección 3.** Completar el notebook con configuración, fábricas de U-Net, U-Net++ y SegFormer-B0, ejecución controlada, historial y tabla de experimentos.
- [ ] **P2-3 — Verificar y documentar la entrega.** Ejecutar pruebas sintéticas/cortas, comprobar que `test` no se usa durante entrenamiento y documentar formatos, límites y comandos de ejecución.

## Criterios de aceptación

- Los tres modelos producen logits finitos con forma `(B, 1, H, W)` tras el adaptador común.
- La pérdida Dice + BCE permite una pasada forward/backward.
- El loop selecciona el mejor checkpoint por Dice de validación y soporta early stopping.
- El historial y la tabla de experimentos tienen un esquema estable y se guardan fuera de rutas ignoradas cuando corresponda.
- El notebook puede ejecutarse en modo de prueba sin entrenar los tres modelos completamente.
- La entrega explica que los pesos finales requieren una ejecución prolongada o hardware acelerado.

## Verificaciones aplicables

- Importación y compilación de los módulos modificados.
- Pruebas unitarias o sintéticas del cálculo de pérdida, adaptación de salida, checkpoint y early stopping.
- Prueba de humo de los tres modelos con entradas pequeñas, sin descargar pesos cuando se pruebe offline.
- Inspección estructural del notebook y ejecución de sus celdas de entrenamiento en modo seguro.

## Progreso y evidencia

- Estado inicial verificado: 351 TIFF, `splits.csv` con 245/53/53, sin `cache_768`, checkpoints ni dependencias de modelos.
- Rama de trabajo: `feat/persona-2-training`.
- P2-1 completada: `src/training.py` contiene el flujo común y `tests/test_training.py` cubre pérdida/backward, adaptación de SegFormer, métricas ponderadas, early stopping y checkpoints.
- Verificación P2-1: `uv run python -m unittest tests/test_training.py -v` (5 pruebas, OK), `uv run python -m compileall src tests` (OK) y `git diff --check` (OK).
- Commit P2-1: `0851ea4` (`feat(training): add reusable segmentation training loop`). Evaluación RDD: riesgo medio por cambio de dependencias, diferida al cierre de la porción de entrega.
- Estrategia de cadena elegida: PRs apiladas hacia `main`; cada unidad debe poder verificarse e integrarse en orden.
- P2-2 completada sin ejecutar entrenamiento ni descargar pesos: fábricas offline para los tres modelos, sección 3 con banderas seguras, artefactos estables y uso completo del último lote de entrenamiento.
- Verificación P2-2: 8 pruebas unitarias y de humo en CPU (OK), compilación de `src` y `tests` (OK), 16 celdas de código del notebook compiladas y sección 3 sin acceso al cargador de prueba, `git diff --check` (OK).
- Próximo paso: P2-3.

## Estimación de entrega

La implementación puede superar aproximadamente 400 líneas debido a las tres integraciones, pruebas y notebook. Se priorizarán unidades coherentes sin sacrificar claridad ni validación; la estrategia `ask-on-risk` se aplicará antes de exceder el presupuesto de entrega.
