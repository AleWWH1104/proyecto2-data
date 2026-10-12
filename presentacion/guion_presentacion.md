# Guion de presentación: resultados y aplicación

Guion listo para ensayar con `presentacion.pdf`, no para repetir entrenamiento.
La presentación ya existía: se conservan sus 20 páginas, orden, tema y cifras.
El informe final y cuatro capturas auténticas están completos. Faltan pesos,
metadatos completos y caché; la entrega externa y permisos de Drive no están confirmados.
Los resultados son históricos: no se ejecutaron modelos ni se reevaluaron imágenes
para preparar esta exposición. Es un prototipo de investigación, no clínico.

## Preparación y reparto propuesto

No se encontró un guion anterior. Los documentos `docs/division_avances_resultados.md`
y `docs/division_aplicacion.md` son planes de trabajo, no libretos; se toma solo
la idea de tres roles. No hay correspondencia confirmada entre roles y autores.
El equipo debe asignarlos entre Iris Ayala, Jonatan Díaz y Anggie Quezada.

- **Rol A:** problema, datos y entrada; páginas PDF 1–5.
- **Rol B:** modelos, entrenamiento registrado y métricas; páginas 6–11.
- **Rol C:** análisis por órgano, aplicación y cierre; páginas 12–18.
- **Referencias:** páginas 19–20 como respaldo, sin leer toda la bibliografía.

**Propuesta de ensayo, no tiempo exigido por el docente:** 12 minutos de narración
y navegación, incluidos 90 segundos de demo. Las metas de la tabla suman 720 segundos;
ajustar después de un ensayo cronometrado. No incluyen preguntas del público.
La portada no tiene número visible; página PDF 2 corresponde a 1/19 y PDF 20 a 19/19.

| PDF | Visible | Título exacto | Mensaje central | Rol | Meta (s) |
| --- | --- | --- | --- | --- | ---: |
| 1 | — | Resultados y aplicación | Alcance y estado real | A | 20 |
| 2 | 1/19 | Problema, objetivo y resultado principal | FTU binaria, no órgano | A | 35 |
| 3 | 2/19 | Datos y EDA que orientan la interpretación | Desbalance y contexto | A | 40 |
| 4 | 3/19 | Split reproducible y límites de fuga de información | 245/53/53, límite por donante | A | 40 |
| 5 | 4/19 | Entrada compartida: de la histología al tensor | RGB/384/ImageNet | A | 40 |
| 6 | 5/19 | Tres modelos: comparación controlada | Tres arquitecturas, misma entrada | B | 40 |
| 7 | 6/19 | Perfil conservador realmente utilizado | Configuración registrada | B | 35 |
| 8 | 7/19 | Historial: el mejor checkpoint no es la última época | 13/8, 6/1, 10/5 | B | 35 |
| 9 | 8/19 | Curvas registradas de entrenamiento y validación | Generalización no garantizada | B | 30 |
| 10 | 9/19 | Cómo leer las métricas y el tiempo | Solapamiento y forward GPU | B | 45 |
| 11 | 10/19 | Resultados globales en las 53 imágenes de prueba | SegFormer 0.629/0.510 | B | 40 |
| 12 | 11/19 | El órgano cambia la lectura del promedio | No basta el promedio | C | 30 |
| 13 | 12/19 | Desglose: tamaños pequeños y diferencias descriptivas | Pulmón limita el alcance | C | 40 |
| 14 | 13/19 | Selección: SegFormer como opción de referencia | Referencia de esta ejecución | C | 35 |
| 15 | 14/19 | Demostración honesta: cuatro páginas implementadas | CSV útiles sin pesos | C | 110 |
| 16 | 15/19 | Nueva imagen: flujo disponible al recuperar los pesos | Implementado no es aceptado | C | 35 |
| 17 | 16/19 | Límites y pendientes de entrega | Límites científicos y operativos | C | 30 |
| 18 | 17/19 | Conclusiones y acciones de entrega | Entrega sin pesos explícita | C | 30 |
| 19 | 18/19 | Referencias: contexto y arquitecturas | Respaldo bibliográfico | C | 5 |
| 20 | 19/19 | Referencias: transformer y preprocesamiento | Cierre y preguntas | C | 5 |

## Texto para decir y señales de exposición

Las citas entre comillas son texto hablado. Las indicaciones en cursiva no se leen.
La tabla orienta el ensayo; no convierte la duración en una medición ya realizada.

### PDF 1 — Resultados y aplicación

“Buenos días. Presentamos la comparación de tres modelos para segmentar unidades
funcionales de tejido y una aplicación para explorar sus resultados. El informe
está completo; la demo local no cuenta con pesos entrenados. Mostraremos esa
limitación sin simular predicciones.”

*Señalar autores; transición: «Primero, qué problema resolvemos».*

### PDF 2 — Problema, objetivo y resultado principal

“Buscamos una máscara que indique FTU frente a fondo en una imagen histológica.
No clasificamos el órgano: ese dato es descriptivo. Comparamos tres arquitecturas
con la misma entrada y split. SegFormer obtuvo el mayor Dice medio registrado,
0.629, pero eso no significa validación clínica ni superioridad universal.”

*Señalar el bloque binario; transición: «La composición de los datos importa».*

### PDF 3 — Datos y EDA que orientan la interpretación

“Son 351 imágenes etiquetadas de fuente HPA, distribuidas en cinco órganos.
Riñón tiene 99 imágenes y pulmón 48; las cantidades no son iguales. El EDA previo
registró una mediana de cobertura FTU de 5.9 por ciento: es mediana por imagen,
no porcentaje de todos los píxeles. Este contexto ayuda a interpretar, no demuestra
causas. Hoy no disponemos de train.csv para explorar todos esos metadatos.”

*Señalar cantidades y aviso de fuente; transición: «Cómo se separaron».*

### PDF 4 — Split reproducible y límites de fuga de información

“El split estratificado por órgano conserva 245 imágenes de entrenamiento,
53 de validación y 53 de prueba, con semilla 42. El checkpoint se elige por
validación y el umbral queda fijo. Aquí solo leemos resultados de prueba ya
guardados. Como la separación es por imagen, no podemos afirmar independencia
por donante o laboratorio.”

*Señalar fila Total; transición: «Qué entra realmente al modelo».*

### PDF 5 — Entrada compartida: de la histología al tensor

“La entrada se convierte a RGB y se lleva a 384 por 384 píxeles con normalización
ImageNet. Las máscaras usan vecino más cercano para conservar etiquetas.
La aumentación aleatoria corresponde solo al entrenamiento. Edad, sexo y órgano
no son entradas del modelo; la máscara es el objetivo. La referencia física es
0.4 micrómetros por píxel, no una medida inferida de cualquier carga nueva.”

*Transición al rol B: «Con esa entrada común comparamos tres arquitecturas».*

### PDF 6 — Tres modelos: comparación controlada

“U-Net con ResNet34 es la línea base encoder–decoder. U-Net++ conserva ResNet34
y rediseña conexiones para combinar escalas. SegFormer usa MIT-B0, un transformer
jerárquico con decoder ligero. Los tres producen un canal binario y comparten
resolución, split, pérdida y umbral. Comparamos estas ejecuciones, no todo el
potencial de las familias.”

*Señalar los tres nombres; transición: «Veamos las condiciones registradas».*

### PDF 7 — Perfil conservador realmente utilizado

“El perfil registrado usó batch físico uno y acumulación de dos pasos: batch
efectivo dos. Incluyó AMP CUDA, AdamW con learning rate diez a la menos cuatro,
weight decay diez a la menos dos y pérdida Dice más BCE. El máximo fue veinte
épocas con paciencia cinco. Es una ejecución Windows en RTX 4060 Laptop;
no entrenamos nuevamente para preparar la entrega.”

*Transición: «El máximo solicitado no equivale a las épocas ejecutadas».*

### PDF 8 — Historial: el mejor checkpoint no es la última época

“U-Net ejecutó trece épocas y su mejor checkpoint fue el ocho. U-Net++ ejecutó
seis y su mejor fue el uno; no terminó en la primera época. SegFormer ejecutó
diez y su mejor fue el cinco. Son veintinueve épocas registradas en total.
La detención temprana no demuestra que el ruido causara el resultado ni establece
el techo de U-Net++.”

*Señalar columnas distintas; transición: «Las curvas muestran esa diferencia».*

### PDF 9 — Curvas registradas de entrenamiento y validación

“La línea punteada corresponde a entrenamiento, la continua a validación y el
círculo marca la mejor época. Mejorar en entrenamiento no garantiza mejorar
en validación. Estas curvas son el historial existente, no réplicas ni un nuevo
experimento. No atribuimos una causa específica a la divergencia observada.”

*Señalar leyenda y un círculo, sin recorrer cada punto; transición: «Cómo evaluamos».*

### PDF 10 — Cómo leer las métricas y el tiempo

“Dice e IoU miden solapamiento entre máscara predicha y anotación; uno es mejor
y cero indica ausencia de solapamiento. Dice usa dos veces la intersección sobre
la suma de áreas; IoU usa la intersección sobre la unión. Reportamos medias por
imagen para 53 IDs comunes, 159 registros. El tiempo mide solo forward GPU,
sin carga ni preprocesamiento; no es latencia total ni un benchmark de este Mac.”

*Señalar denominadores; transición: «Con esa definición, estos son los resultados».*

### PDF 11 — Resultados globales en las 53 imágenes de prueba

“U-Net registra Dice 0.506 e IoU 0.400; U-Net++ 0.481 y 0.355; SegFormer 0.629
y 0.510. Los forward medios registrados son 11.8, 31.9 y 11.6 milisegundos,
respectivamente, en RTX 4060 Laptop. La diferencia de 0.2 milisegundos entre
SegFormer y U-Net no basta para afirmar superioridad de velocidad.”

*Señalar tabla; transición al rol C: «El promedio oculta diferencias por órgano».*

### PDF 12 — El órgano cambia la lectura del promedio

“SegFormer tiene el mayor Dice medio en los cinco órganos de este registro.
Sin embargo, pulmón sigue mostrando el menor solapamiento para los tres modelos.
Por eso, un promedio global favorable no significa buen desempeño en cada grupo.”

*Señalar pulmón y contraste con riñón; transición: «Veamos tamaños y cifras».*

### PDF 13 — Desglose: tamaños pequeños y diferencias descriptivas

“Los grupos de prueba van de quince imágenes de riñón a siete de pulmón.
En pulmón los Dice son 0.042, 0.061 y 0.103: el desempeño sigue siendo limitado.
La cobertura del EDA aporta contexto, pero no demuestra por qué fallan los modelos.
Sin intervalos de confianza ni ejecuciones repetidas, estas son diferencias
descriptivas; no afirmamos significancia estadística.”

*Señalar n y última fila; transición: «Qué selección sí permite esta evidencia».*

### PDF 14 — Selección: SegFormer como opción de referencia

“Elegimos SegFormer como referencia de esta ejecución por su mejor Dice de
validación, 0.6596, y los resultados registrados. El checkpoint se seleccionó
con validación, no con prueba. Mantenemos los otros modelos como comparadores.
Esta recomendación no prueba transferencia a otros laboratorios ni uso clínico.”

*Transición: «Ahora mostraremos lo que la aplicación permite comprobar hoy».*

### PDF 15 — Demostración honesta: cuatro páginas implementadas

“La aplicación tiene Inicio, Exploración, Predicción y Rendimiento. Sin pesos
podemos navegar metadatos disponibles y resultados CSV. Predicción comunica
el bloqueo real. Mostrar rendimiento es una preferencia persistente: oculta
los resultados, no los borra ni cambia.”

*Usar la ruta de demo siguiente durante 90 segundos; volver al PDF antes de avanzar.*

### PDF 16 — Nueva imagen: flujo disponible al recuperar los pesos

“El flujo implementado acepta PNG, JPEG o TIFF de una imagen, hasta 64 MiB
y nueve millones de píxeles. Con pesos confiables produciría máscara binaria,
superposición cian, porcentaje FTU y forward CPU. Si falta espaciado, declara
la suposición de 0.4 micrómetros por píxel. Sin máscara de referencia no hay
Dice o IoU de la carga. Implementación y pruebas sintéticas no equivalen a
aceptación con checkpoints reales.”

*No cargar imágenes; transición: «Qué límites permanecen».*

### PDF 17 — Límites y pendientes de entrega

“Tenemos una ejecución por modelo, una muestra pequeña y ninguna incertidumbre
cuantificada. El split no valida independencia por donante ni transferencia
HPA a HuBMAP. Tampoco estudiamos otras resoluciones. Informe y capturas están
completos; faltan activos locales y la entrega humana externa. No es una
herramienta para diagnóstico.”

*Señalar el estado actualizado; transición: «Concluimos sin ocultar estos límites».*

### PDF 18 — Conclusiones y acciones de entrega

“La comparación registrada favorece a SegFormer, pero el promedio no sustituye
el análisis por órgano. La aplicación permite mostrar exploración y resultados
sin simular inferencia. Entregamos informe y presentación completos, con pesos
y aceptación real diferidos. Falta confirmar Drive y permisos y realizar la
entrega humana. Recuperar activos requerirá autorización separada.”

*Cerrar el argumento antes de referencias; no prometer tiempos de entrenamiento.*

### PDF 19 — Referencias: contexto y arquitecturas

“Dejamos estas fuentes como respaldo del contexto y las arquitecturas.”

*No leer bibliografía completa; mantener disponible si hay preguntas sobre fuentes.*

### PDF 20 — Referencias: transformer y preprocesamiento

“Aquí están las fuentes de SegFormer y preprocesamiento. Gracias; recibimos preguntas.”

*No afirmar que las cinco referencias de estas diapositivas son las 18 del informe.*

## Demo propuesta: 90 segundos incluidos en PDF 15

Antes de exponer, desde la raíz, abrir la aplicación con `uv run streamlit run app/Inicio.py`
y dejar listas sus cuatro páginas. Este es un paso de preparación manual, no un
comando de entrenamiento. Usar el puerto indicado por Streamlit. No ejecutar notebooks,
scripts de figuras, entrenamiento o evaluación ni abrir imágenes del split de prueba.

1. **0–15 s, Inicio:** señalar resumen y avisos de activos faltantes.
   Decir: “Los CSV existen; los checkpoints no están en este checkout”.
2. **15–30 s, Exploración:** mostrar órganos y splits, un filtro y restablecerlo.
   Decir: “Tenemos 351 registros de splits.csv; sin train.csv no mostramos
   edad, dimensiones, fuente o cobertura como datos recuperados”.
3. **30–60 s, Rendimiento:** elegir **Todos**, un órgano y alternar **DICE/IOU**;
   volver a todos los órganos y señalar comparación y curvas.
   Decir: “Son resultados guardados; el filtro por órgano no cambia el historial”.
   Desactivar **Mostrar rendimiento**, volver a Inicio y señalar que sigue oculto;
   reactivarlo. No describir dispersión como intervalo de confianza.
4. **60–80 s, Predicción:** mostrar el aviso de bloqueo por pesos ausentes.
   Decir: “No cargaremos imágenes ni inventaremos una máscara. El flujo está
   implementado, pero su aceptación con pesos reales está diferida”.
5. **80–90 s:** volver al PDF y enlazar con el flujo de nueva imagen.

**Respaldo si falla la aplicación:** mostrar las capturas auténticas existentes
`informe/figuras/app_inicio.png`, `app_exploracion.png`, `app_rendimiento.png`
y `app_prediccion.png`. Anunciar: “Son capturas del estado local previamente
registrado, no una demo en vivo ni evidencia de inferencia”. No fabricar pantallas.

## Preguntas previsibles

- **¿Por qué faltan pesos si hay métricas?** Los CSV conservan resultados históricos;
  los checkpoints son archivos separados, excluidos de Git y no recuperados aquí.
  Tener métricas no permite reconstruir los parámetros ni generar una predicción.
- **¿Por qué SegFormer?** Obtuvo el mayor mejor Dice de validación y las mayores
  medias registradas. Es referencia de este split/perfil, no superioridad estadística.
- **¿Qué diferencia hay entre Dice e IoU?** Ambos comparan máscaras; Dice divide
  dos veces la intersección entre la suma de áreas, IoU entre la unión.
  Se promedian por imagen, no sobre un único conjunto agregado de píxeles.
- **¿Por qué es bajo pulmón?** El registro muestra bajo solapamiento en siete
  imágenes. El EDA contextualiza; no tenemos evidencia para aislar una causa.
- **¿Se evitó toda fuga?** El split por imagen y selección por validación son
  controles; no prueban separación por donante, laboratorio ni independencia total.
- **¿Cuánto tarda en CPU o entrenar de nuevo?** No hay medición aceptada de CPU
  con pesos locales ni duración total aquí. Los milisegundos publicados son forward
  de RTX 4060 Laptop, no CPU, latencia completa ni minutos de entrenamiento.
- **¿Está todo terminado?** Informe, presentación y demo de CSV están listos.
  Pesos, metadatos completos, caché y aceptación real están diferidos; permisos
  de Drive y entrega humana externa permanecen pendientes. No afirmar toda la rúbrica cumplida.
- **¿Sirve clínicamente o en HuBMAP externo?** No. No se validó transferencia
  de dominio, incertidumbre ni uso clínico; es un prototipo de investigación.

## Comprobación antes de hablar

- Asignar los tres roles sin inferir responsabilidades históricas por nombre.
- Ensayar la propuesta de 12 minutos y confirmar el tiempo real permitido por el docente.
- Abrir PDF y aplicación o las capturas de respaldo; comprobar permisos solo por canal autorizado.
- Conservar CSV y figuras; no regenerarlos para mejorar la exposición.
- Mantener explícitos los pendientes: sin pesos no hay predicción nueva demostrada.
