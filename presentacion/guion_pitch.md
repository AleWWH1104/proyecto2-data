# Guion de presentación — Reto 18: HuBMAP

División equitativa: **5 diapositivas de contenido por persona** (Iris abre con la portada, Anggie cierra con agradecimientos).

---

## Iris Ayala — Introducción y datos (diaps. 2 a 6)

**Diap. 1 — Portada**

> "Buenas [tardes/días]. Somos Iris Ayala, Jonatan Díaz y Anggie Quezada, y les vamos a presentar el análisis exploratorio del Reto 18: Hackeando el cuerpo humano, el proyecto HuBMAP sobre segmentación de unidades funcionales de tejido."

**Diap. 2 — Introducción y base conceptual**

- HuBMAP busca mapear el cuerpo humano a nivel de célula.
- Una FTU (unidad funcional de tejido) es un grupo de células alrededor de un vaso sanguíneo que cumple una función dentro del órgano — el reto cubre cinco órganos y en cada uno la FTU se ve distinta (glomérulos en riñón, criptas en intestino, etc.).
- Las muestras se tiñen con PAS, por eso las imágenes se ven en tonos rosado/morado.
- Hoy esas FTU las marca un patólogo a mano, al microscopio: es lento, subjetivo y no escala. Y para complicarlo más, muestras del mismo órgano preparadas en laboratorios distintos no se ven igual.

**Diap. 3 — Problema científico y objetivos**

- Pregunta de investigación: a partir de una imagen de tejido, ¿se puede entrenar un modelo que marque con precisión dónde están las FTU, sin importar el órgano ni la fuente de la muestra?
- Objetivo general: explorar y describir los datos para entender cómo están compuestas las imágenes y las variables, como base para una futura solución de segmentación.
- Objetivos específicos: describir variables y detectar diferencias entre grupos; analizar cómo se relacionan órgano, fuente, edad y sexo; cuantificar el área que ocupa la FTU entre órganos.

**Diap. 4 — Qué tenemos**

- `train.csv` tiene 351 observaciones (una por imagen), 10 variables, cero nulos y cero duplicados.
- La única limpieza necesaria fue convertir `organ`, `data_source` y `sex` a tipo categórico — el dataset llegó muy limpio.
- Repasar rápido la tabla: identificador, tres categóricas, dimensiones de imagen, `pixel_size`, `tissue_thickness`, `age`, y `rle` como texto que guarda la máscara.

**Diap. 5 — La columna `rle`**

- La máscara de la FTU no viene como imagen, viene comprimida en run-length encoding: pares de (posición inicial, longitud).
- Por qué importa: guardar una máscara de 3000×3000 píxeles como matriz sería inviable en una celda de texto; el rle la reduce a unos miles de caracteres.
- De ahí construimos `mask_frac`: píxeles marcados como FTU dividido entre el área total de la imagen. Basta sumar las longitudes, sin reconstruir la máscara completa.

_Transición:_ "Con esa base de los datos, le paso a Jonatan para que les cuente lo que encontramos al explorar las variables una por una y en pares."

---

## Jonatan Díaz — Análisis exploratorio (diaps. 7 a 11)

**Diap. 6 — Variables univariadas**

- Edad va de 21 a 84 años, con mediana en 60.
- Casi todas las imágenes son de 3000×3000 píxeles.
- La proporción de FTU (`mask_frac`) está sesgada a la derecha: la mediana es de apenas 0.059, es decir, en la mayoría de imágenes la FTU ocupa una fracción muy pequeña.

**Diap. 7 — Variables categóricas**

- Hay desbalance por órgano: 99 riñones contra solo 48 pulmones.
- También por sexo: 229 hombres contra 122 mujeres.
- Y algo llamativo: `data_source` tiene una sola barra, es decir, una sola categoría presente en todo el dataset — volvemos a esto más adelante porque tiene una implicación importante.

**Diap. 8 — Cruces por órgano**

- Próstata es 100% masculino, lo cual es biología normal, no un error de los datos.
- Intestino grueso tiene una mediana de edad de 83 años, contra 57-59 años del resto de órganos: esto muestra que órgano y edad no son variables independientes entre sí.

**Diap. 9 — Outliers**

- En `age` hay 13 outliers, todos con valor 21 años — pero 21 cae dentro del rango normal para pulmón y bazo, así que son atípicos solo si se ignora el órgano.
- En `img_height` hay 25 outliers: el 75% de las imágenes mide exactamente 3000 px, entonces el rango intercuartílico es cero y el método de outliers marca todo lo que no sea 3000 — la variable es casi binaria, no continua.
- En ambos casos documentamos el hallazgo pero no eliminamos nada; tampoco hay valores faltantes en las 351 filas.

**Diap. 10 — Hallazgo 1: variables que no dicen nada**

- `pixel_size` (0.4) y `tissue_thickness` (4.0) son constantes en las 351 filas, varianza cero — por eso salen como NaN en la matriz de correlación, no es un bug del código.
- Además, `img_height` es igual a `img_width` siempre: las imágenes son cuadradas, y 326 de 351 son exactamente 3000×3000.
- Conclusión: de las variables tabulares, solo `organ`, `sex`, `age` y la derivada del `rle` (`mask_frac`) aportan información real.

_Transición:_ "Ahora Anggie va a mostrarles el hallazgo más importante del análisis: una paradoja que casi nos hace sacar una conclusión equivocada, y cómo cerramos el análisis."

---

## Anggie Quezada — Hallazgos multivariados y conclusiones (diaps. 12 a 16, + cierre)

**Diap. 11 — Hallazgo 2: la FTU no ocupa lo mismo en cada órgano**

- La mediana de `mask_frac` por órgano va de 19.6% en intestino grueso a apenas 1.3% en pulmón — la mediana global es 5.9%.
- Eso es una diferencia de quince veces entre el órgano con más FTU y el que tiene menos.
- Encontrar la FTU no es el mismo problema en cada órgano: un modelo que funcione bien en intestino grueso puede fallar completamente en pulmón.

**Diap. 12 y 13 — Hallazgo 3: la paradoja de Simpson**

- Si calculamos la correlación global entre edad y tamaño de FTU, sale +0.248 — parecería que a mayor edad, mayor FTU.
- Pero si estratificamos por órgano, la correlación cambia de signo o se vuelve prácticamente nula en varios: riñón -0.178, pulmón -0.396, próstata y bazo casi cero.
- La razón: intestino grueso tiene a la vez los donantes más viejos y las FTU más grandes, entonces al mezclar todos los órganos ese grupo arrastra la correlación global hacia arriba — la correlación global no mide edad contra FTU, mide el órgano disfrazado.
- Implicación clave: cualquier correlación calculada sobre este conjunto sin estratificar por órgano es poco confiable.

**Diap. 14 — Hallazgo 4: el desbalance está en varios ejes a la vez**

- Desbalance por órgano (99 riñones vs 48 pulmones), por sexo (229 hombres vs 122 mujeres) y por edad (concentrada entre 55 y 73 años).
- Y no son independientes entre sí: los 93 casos de próstata son todos masculinos, e intestino grueso concentra a los donantes de mayor edad.
- El desbalance de un eje se filtra en los otros — no se pueden tratar por separado.

**Diap. 15 — Hallazgo 5: la dificultad del reto no está en los datos**

- Las 351 filas de `train.csv` tienen `data_source = HPA`; no hay ni una sola observación de HuBMAP en el set de entrenamiento.
- Las muestras de HuBMAP quedan del lado del conjunto de prueba de la competencia.
- Pero la dificultad central del reto es justamente que el modelo funcione con muestras preparadas en laboratorios distintos — esa variabilidad no se puede observar ni medir dentro de los datos de entrenamiento que tenemos.

**Diap. 16 — Siguientes pasos / Conclusiones**

- Descartar `pixel_size` y `tissue_thickness`: no discriminan nada.
- Tratar esto como segmentación desbalanceada: con solo 5.9% de píxeles positivos, predecir fondo en toda la imagen daría más de 94% de exactitud por píxel y sería un modelo inútil — hay que usar métricas como Dice o IoU, no exactitud.
- Validar por órgano y no solo en global, porque el promedio esconde que pulmón y riñón son mucho más difíciles.
- Estratificar todo análisis por órgano, como lo demostró la paradoja de Simpson.
- Apoyarse en aumentación de color y tinción, la única vía para simular la variabilidad entre fuentes que el entrenamiento no contiene.

**Diap. 17 — Cierre**

> "Con esto cerramos el análisis exploratorio del Reto 18. El código completo está en nuestro repositorio de GitHub, AleWWH1104/proyecto2-data. Muchas gracias."

---
