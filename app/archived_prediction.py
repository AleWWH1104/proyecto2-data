"""Archived prediction interface, excluded from Streamlit page discovery."""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comun import CHECKPOINTS, MODELO_SELECCIONADO, NOMBRES_COMPLETOS
from src.inference import (
    InferenceError, available_checkpoints, decode_upload, load_model, predict,
)


def main():
    st.title("Predicción de unidades funcionales de tejido")
    st.warning("Uso exclusivo para investigación. No es una herramienta de diagnóstico médico.")
    st.caption(
        "Los modelos generan una máscara binaria de FTU, no clasifican órganos. "
        "El órgano indicado es información proporcionada por el usuario."
    )
    organ = st.selectbox(
        "Órgano de la imagen", ["Riñón", "Próstata", "Intestino grueso", "Bazo", "Pulmón"],
    )
    with st.expander("Preprocesamiento y límites"):
        st.write(
            "PNG, JPEG o TIFF de una sola imagen; máximo 64 MiB, 9 millones de píxeles "
            "y 8192 píxeles por lado (mínimo 2). Conversión a RGB de 8 bits; "
            "los valores de 16 bits se escalan por mínimo y máximo globales. "
            "Se descarta el canal alfa. Se asumen 0.4 µm/píxel: otra escala puede afectar el resultado. "
            "Redimensionamiento de caché a 384 × 384 y normalización ImageNet, "
            "sin aumentación. Umbral fijo ≥ 0.5; máscara binaria restaurada por vecino más cercano."
        )
    available = available_checkpoints(CHECKPOINTS)
    for name in NOMBRES_COMPLETOS:
        if name not in available:
            st.info(
                f"Falta {name}.pt para {NOMBRES_COMPLETOS[name]}. "
                "Recupere los pesos existentes; no se simulan resultados."
            )
    upload = st.file_uploader(
        "Subir una imagen nueva", type=["png", "jpg", "jpeg", "tif", "tiff"],
    )
    if not available:
        st.warning("No hay checkpoints disponibles. La predicción está bloqueada hasta recuperar los archivos.")
        return
    choices = list(available)
    default = choices.index(MODELO_SELECCIONADO) if MODELO_SELECCIONADO in choices else 0
    choice = st.selectbox(
        "Modelo", choices + ["all"], index=default,
        format_func=lambda value: (
            "Todos los modelos disponibles" if value == "all" else NOMBRES_COMPLETOS[value]
        ),
    )
    if upload is None:
        st.info("Suba una imagen nueva para habilitar la predicción.")
        return
    try:
        rgb = decode_upload(upload.getvalue())
    except InferenceError as error:
        st.error(str(error))
        return
    st.image(rgb, caption=f"Imagen original — {organ}")
    if not st.button("Generar predicción", type="primary"):
        return
    st.caption(
        "Sin máscara real no se calcula Dice, IoU ni exactitud. Tiempo de forward "
        "en CPU, sin carga ni preprocesamiento; no es un benchmark."
    )
    selected = choices if choice == "all" else [choice]
    for name, column in zip(selected, st.columns(len(selected))):
        with column:
            st.subheader(NOMBRES_COMPLETOS[name])
            try:
                with st.spinner("Procesando en CPU…"):
                    # Sequential loading bounds memory; do not cache all three models.
                    model = load_model(name, available[name])
                    try:
                        result = predict(model, rgb)
                    finally:
                        del model
                st.image(result.overlay, caption=f"FTU superpuestas — {organ}")
                st.image(result.mask * 255, caption="Máscara binaria: blanco = FTU", clamp=True)
                st.metric("Área predicha como FTU", f"{result.coverage_percent:.2f} %")
                st.metric("Tiempo de inferencia (CPU)", f"{result.seconds:.3f} s")
            except Exception as error:
                message = str(error) if isinstance(error, InferenceError) else (
                    "La salida del modelo no cumple el contrato esperado. "
                    "No se generó una predicción."
                )
                st.error(message)


main()
