"""Explore existing tabular metadata without accessing dataset images."""

import plotly.express as px
import streamlit as st

from comun import cargar_datos

st.set_page_config(page_title="Exploración", page_icon="🔬", layout="wide")
st.title("Exploración de los datos")
st.info(
    "Los modelos reciben píxeles RGB a 384 × 384 con normalización ImageNet. "
    "Órgano, edad, sexo y fuente son variables descriptivas, no entradas del modelo."
)
data = cargar_datos()
frame = data["train"]
if frame.empty:
    st.info("train.csv no está disponible o es inválido. Se muestran únicamente los metadatos de splits.csv.")
    frame = data["splits"]
    st.caption("Este CSV describe las particiones; no contiene edad, fuente, dimensiones ni cobertura FTU.")
else:
    st.caption("Fuente: train.csv, metadatos disponibles; no se abren imágenes ni se decodifican máscaras.")
for issue in data["issues"]:
    if issue.startswith(("train.csv:", "splits.csv:")):
        st.caption(issue)
if frame.empty:
    st.info("No hay metadatos tabulares válidos para explorar.")
    st.stop()

for column, label in [("organ", "Órgano"), ("split", "Partición"), ("data_source", "Fuente"), ("sex", "Sexo")]:
    if column in frame:
        options = sorted(frame[column].dropna().astype(str).unique())
        chosen = st.sidebar.multiselect(label, options, default=options, key=f"eda_{column}")
        frame = frame[frame[column].astype(str).isin(chosen)]
if frame.empty:
    st.info("No hay filas para los filtros seleccionados.")
    st.stop()
st.metric("Imágenes descritas por los metadatos filtrados", len(frame))
for column, title in [("organ", "Distribución por órgano"), ("split", "Particiones"), ("data_source", "Fuente del dataset")]:
    if column in frame:
        counts = frame[column].fillna("Sin dato").value_counts().rename_axis(column).reset_index(name="Imágenes")
        st.plotly_chart(px.bar(counts, x=column, y="Imágenes", title=title), width="stretch")
for column, title in [("age", "Edad"), ("pixel_size", "Resolución espacial (µm/píxel)"),
                      ("proporcion_ftu", "Proporción FTU [0, 1]")]:
    if column in frame and frame[column].notna().any():
        st.plotly_chart(px.histogram(frame, x=column, color="organ", barmode="overlay", title=title), width="stretch")
if {"img_width", "img_height"}.issubset(frame.columns):
    st.plotly_chart(px.scatter(frame, x="img_width", y="img_height", color="organ",
                               title="Dimensiones originales (píxeles)"), width="stretch")
st.caption(
    "La cobertura FTU, cuando está disponible, se calcula de las longitudes RLE del CSV, "
    "sin leer imágenes. Las diferencias de cantidad, escala y cobertura pueden contextualizar "
    "errores por órgano, pero no demuestran su causa. Consulte Rendimiento para las métricas registradas."
)
st.dataframe(frame.drop(columns=["rle"], errors="ignore"), hide_index=True, width="stretch")
