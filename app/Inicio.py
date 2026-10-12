"""Portada de la aplicación. Se corre con: uv run streamlit run app/Inicio.py"""

import streamlit as st

from comun import NOMBRES_COMPLETOS, archivos_faltantes, cargar_datos, paired_metrics, performance_visible

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

if performance_visible():
    datos = cargar_datos()
    models = list(NOMBRES_COMPLETOS)
    paired, excluded = paired_metrics(datos["metricas"], models)
    st.subheader("Resultados existentes")
    if paired.empty:
        st.warning("No hay métricas válidas comunes para los tres modelos.")
    else:
        st.caption(f"Evaluación registrada: {paired['id'].nunique()} imágenes comunes; no se reevalúa.")
        resumen = paired.groupby("modelo")[["dice", "iou"]].mean()
        for columna, modelo in zip(st.columns(len(models)), models):
            with columna:
                st.metric(NOMBRES_COMPLETOS[modelo], f"Dice {resumen.loc[modelo, 'dice']:.3f}")
                st.caption(f"IoU {resumen.loc[modelo, 'iou']:.3f} · rango [0, 1]")
        if excluded:
            st.warning(f"Se excluyen {excluded} filas sin pareja para comparar el mismo conjunto.")
    st.caption("Promedios descriptivos, sin intervalos de confianza; detalles en Rendimiento.")

st.subheader("Qué hay en cada página")
st.markdown(
    """
- **Exploración**: las variables del conjunto de datos y los hallazgos del análisis exploratorio.
- **Predicción**: carga una imagen nueva de tejido y compara la segmentación de los modelos disponibles.
- **Rendimiento**: métricas de los modelos en el conjunto de prueba, por órgano y por época.
"""
)

faltantes = archivos_faltantes()
if faltantes:
    st.warning(
        "Faltan archivos del Drive en `data/`: "
        + ", ".join(f"`{f}`" for f in faltantes)
        + ". La exploración usa los metadatos tabulares disponibles; los resultados existentes no requieren pesos."
    )
