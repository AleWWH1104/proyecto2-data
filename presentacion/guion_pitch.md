# Guion de presentación — Reto 18: HuBMAP

Distribución sobre las **22 diapositivas reales** del PDF: el tema metropolis inserta automáticamente una diapositiva separadora por cada `\section{}` (solo el nombre de la sección, sin contenido), además de las 17 diapositivas de contenido (portada + 16 frames). Está escrito como si lo estuvieran hablando — úsenlo de base y adáptenlo a como hablan normalmente.

---

## Iris Ayala — Introducción y datos (diaps. 1 a 7)

**Diap. 1 — Portada**

> Buenas [tardes/días]. Somos Iris Ayala, Jonatan Díaz y Anggie Quezada, y les vamos a presentar el análisis exploratorio que hicimos para el Reto 18, "Hackeando el cuerpo humano", que es la competencia HuBMAP de segmentación de unidades funcionales de tejido.

**Diap. 2 — [Separador] Introducción**

> Empezamos con la introducción y la base conceptual del proyecto.

**Diap. 3 — Introducción y base conceptual**

> El proyecto es sobre HuBMAP, que busca mapear el cuerpo humano a nivel de célula, y una pieza clave de ese mapa son las unidades funcionales de tejido, o FTU, un grupito de células alrededor de un vaso sanguíneo que cumple una función dentro del órgano. Cada uno de los cinco órganos del reto tiene su propia versión de FTU, y las muestras se tiñen con PAS, por eso ese tono rosado y morado en las imágenes.
>
> Hoy esas FTU las marca un patólogo a mano, al microscopio, y eso es lento, subjetivo y no escala. Y para complicarlo más, ni siquiera las muestras del mismo órgano se ven igual entre laboratorios.

**Diap. 4 — Problema científico y objetivos**

> Pregunta de investigación: a partir de una imagen de tejido, ¿podemos entrenar un modelo que marque con precisión dónde están las FTU, sin importar el órgano ni el laboratorio de origen? Nuestro objetivo general fue explorar y describir los datos como base para eso. Los específicos: describir las variables y detectar diferencias entre grupos, analizar cómo se relacionan órgano, fuente, edad y sexo, y cuantificar el área que ocupa la FTU entre órganos.

**Diap. 5 — [Separador] Los datos**

> Ahora sí, vamos a los datos.

**Diap. 6 — Qué tenemos**

> `train.csv` tiene 351 observaciones, una por imagen, y 10 variables — cero nulos, cero duplicados. La única limpieza que hicimos fue convertir `organ`, `data_source` y `sex` a tipo categórico. En la tabla: un identificador, esas tres categóricas, alto y ancho de imagen, tamaño de píxel, grosor del tejido, edad, y `rle`, que guarda la máscara de la FTU — de esa hablamos ahora.

**Diap. 7 — La columna `rle`**

> La máscara de la FTU no viene como imagen, viene comprimida en run-length encoding: pares de (dónde empieza un segmento, cuánto dura). Guardarla completa como matriz de 3000x3000 sería inviable en una celda de texto; el rle la reduce a unos miles de caracteres. De ahí construimos `mask_frac`: la fracción de la imagen ocupada por FTU, sumando las longitudes sin reconstruir la máscara completa.

---

## Jonatan Díaz — Análisis exploratorio (diaps. 8 a 15)

**Diap. 8 — [Separador] Análisis exploratorio**

> Pasamos a la parte de análisis exploratorio.

**Diap. 9 — Variables univariadas**

> La edad va de 21 a 84 años, mediana 60. Casi todas las imágenes son de 3000x3000. Y `mask_frac` está sesgada a la derecha: mediana de apenas 0.059, en la mayoría de imágenes la FTU ocupa una fracción muy pequeña.

**Diap. 10 — Variables categóricas**

> Desbalance por órgano (99 riñones contra 48 pulmones) y por sexo (229 hombres contra 122 mujeres). Y `data_source` tiene una sola barra: todas las filas vienen de una única fuente — volvemos a esto más adelante.

**Diap. 11 — Cruces por órgano**

> Próstata es 100% masculino, biología y no un error. Intestino grueso tiene mediana de edad de 83 años contra 57-59 del resto: órgano y edad no son independientes entre sí.

**Diap. 12 — Outliers**

> En `age`, 13 outliers, todos con 21 años — pero cae dentro del rango normal de pulmón y bazo, así que son atípicos solo si se ignora el órgano. En `img_height`, 25 outliers: el 75% mide exactamente 3000 px, el rango intercuartílico es cero y el método marca todo lo que no sea 3000 — la variable es casi binaria, no continua. En ambos casos documentamos y no eliminamos nada. Tampoco hay valores faltantes.

**Diap. 13 — [Separador] Hallazgos**

> Con eso llegamos a los hallazgos principales.

**Diap. 14 — Hallazgo 1: variables que no dicen nada**

> `pixel_size` (0.4) y `tissue_thickness` (4.0) son constantes en las 351 filas, varianza cero — por eso salen NaN en la matriz de correlación, no es un bug del código. `img_height` es siempre igual a `img_width`: las imágenes son cuadradas, y 326 de 351 son de 3000x3000. De las variables tabulares, solo `organ`, `sex`, `age` y `mask_frac` aportan información real.

**Diap. 15 — Hallazgo 2: la FTU no ocupa lo mismo en cada órgano**

> La mediana de `mask_frac` va de 19.6% en intestino grueso a apenas 1.3% en pulmón — global: 5.9%. Quince veces de diferencia. Encontrar la FTU no es el mismo problema en cada órgano.

---

## Anggie Quezada — Hallazgos multivariados y conclusiones (diaps. 16 a 22)

**Diap. 16 y 17 — Hallazgo 3: la paradoja de Simpson**

> La correlación global entre edad y tamaño de FTU es +0.248. Pero estratificada por órgano: riñón -0.178, pulmón -0.396, próstata y bazo casi cero. La razón: intestino grueso tiene a la vez a los donantes más viejos (mediana 83) y las FTU más grandes (19.6%), y arrastra la correlación global hacia arriba. Es la paradoja de Simpson: la correlación global mide el órgano disfrazado, no la relación real entre edad y FTU. Cualquier correlación sin estratificar por órgano es poco confiable.

**Diap. 18 — Hallazgo 4: el desbalance está en varios ejes a la vez**

> Desbalance por órgano, sexo y edad, y no son independientes entre sí: los 93 casos de próstata son todos masculinos, e intestino grueso concentra a los donantes de mayor edad. El desbalance de un eje se filtra en los otros.

**Diap. 19 — Hallazgo 5: la dificultad del reto no está en los datos**

> Las 351 filas tienen `data_source = HPA`; no hay ni una observación de HuBMAP en el set de entrenamiento — esas quedan del lado del test de la competencia. La dificultad central del reto es justamente que el modelo funcione entre laboratorios distintos, y esa variabilidad no se puede medir con los datos que tenemos.

**Diap. 20 — [Separador] Conclusiones**

> Y para cerrar, las conclusiones.

**Diap. 21 — Siguientes pasos / Conclusiones**

> Descartar `pixel_size` y `tissue_thickness`, no discriminan nada. Tratar esto como segmentación desbalanceada: con 5.9% de píxeles positivos, predecir solo fondo daría más de 94% de exactitud y sería inútil — usar Dice o IoU. Validar por órgano, no solo en global. Estratificar todo análisis por órgano, como mostró la paradoja de Simpson. Y apoyarse en aumentación de color y tinción para simular la variabilidad entre fuentes que no tenemos en el entrenamiento.

**Diap. 22 — Cierre**

> Muchas gracias.

---
