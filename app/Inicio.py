"""Portada de la aplicación. Se corre con: uv run streamlit run app/Inicio.py"""

import streamlit as st

from comun import MODELO_SELECCIONADO, MODELOS, NOMBRES_COMPLETOS, archivos_faltantes, cargar_datos

st.set_page_config(page_title="Segmentación de FTU", page_icon="🔬", layout="wide")

st.title("Segmentación de unidades funcionales de tejido")
st.caption("Reto 18: Hackeando el cuerpo humano · HuBMAP + HPA · CC3084 Data Science")

st.markdown(
    """
Una **unidad funcional de tejido (FTU)** es un grupo de células organizadas alrededor de un vaso
sanguíneo que cumple una función dentro de un órgano: los glomérulos del riñón, las criptas del
intestino grueso o los alvéolos del pulmón. Esta aplicación usa tres modelos de aprendizaje profundo
para encontrarlas en imágenes de tejido de cinco órganos.
"""
)

datos = cargar_datos()
resumen = datos["metricas"].groupby("modelo")[["dice", "iou"]].mean()

st.subheader("Modelos entrenados")
st.write(
    f"Resultados en el conjunto de prueba ({datos['metricas']['id'].nunique()} imágenes). "
    f"El modelo seleccionado es **{NOMBRES_COMPLETOS[MODELO_SELECCIONADO]}**."
)
columnas = st.columns(len(MODELOS))
for columna, modelo in zip(columnas, MODELOS):
    with columna:
        etiqueta = NOMBRES_COMPLETOS[modelo]
        if modelo == MODELO_SELECCIONADO:
            etiqueta += " ⭐"
        st.metric(etiqueta, f"Dice {resumen.loc[modelo, 'dice']:.3f}")
        st.caption(f"IoU {resumen.loc[modelo, 'iou']:.3f}")

st.subheader("Qué hay en cada página")
st.markdown(
    """
- **Exploración**: las variables del conjunto de datos y los hallazgos del análisis exploratorio.
- **Predicción**: sube una imagen de tejido o elige una de prueba y compara la segmentación de cada modelo.
- **Rendimiento**: métricas de los modelos en el conjunto de prueba, por órgano y por época.
"""
)

faltantes = archivos_faltantes()
if faltantes:
    st.warning(
        "Faltan archivos del Drive en `data/`: "
        + ", ".join(f"`{f}`" for f in faltantes)
        + ". Sin ellos no funcionan la exploración ni la predicción."
    )
