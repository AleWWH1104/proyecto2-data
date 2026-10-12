"""Portada de la aplicación. Se corre con: uv run streamlit run app/Inicio.py"""

import streamlit as st

from comun import NOMBRES_COMPLETOS, cargar_datos, paired_metrics, performance_visible

st.set_page_config(page_title="Segmentación de FTU", page_icon="🔬", layout="wide")

st.title("Segmentación de unidades funcionales de tejido")
st.caption("Reto 18: Hackeando el cuerpo humano · HuBMAP + HPA · CC3084 Data Science")

st.markdown(
    """
Una **unidad funcional de tejido (FTU)** es una organización de tejido que cumple una función
fisiológica: los glomérulos del riñón, las criptas del intestino grueso o los alvéolos del pulmón.
Este panel permite explorar los metadatos de cinco órganos y comparar los resultados registrados
de tres modelos de segmentación.
"""
)

if performance_visible():
    datos = cargar_datos()
    models = list(NOMBRES_COMPLETOS)
    paired, excluded = paired_metrics(datos["metricas"], models)
    st.subheader("Resultados existentes")
    if paired.empty:
        st.info("No hay métricas válidas comunes para los tres modelos.")
    else:
        st.caption(f"Evaluación registrada: {paired['id'].nunique()} imágenes comunes; no se reevalúa.")
        resumen = paired.groupby("modelo")[["dice", "iou"]].mean()
        for columna, modelo in zip(st.columns(len(models)), models):
            with columna:
                st.metric(NOMBRES_COMPLETOS[modelo], f"Dice {resumen.loc[modelo, 'dice']:.3f}")
                st.caption(f"IoU {resumen.loc[modelo, 'iou']:.3f} · rango [0, 1]")
        if excluded:
            st.caption(f"Se excluyen {excluded} filas sin pareja para comparar el mismo conjunto.")
    st.caption("Promedios descriptivos, sin intervalos de confianza; detalles en Rendimiento.")

st.subheader("Qué hay en cada página")
st.markdown(
    """
- **Exploración**: las variables del conjunto de datos y los hallazgos del análisis exploratorio.
- **Rendimiento**: métricas de los modelos en el conjunto de prueba, por órgano y por época.
"""
)

st.caption("Prototipo de investigación. La demo muestra metadatos y resultados históricos; no ejecuta modelos.")
