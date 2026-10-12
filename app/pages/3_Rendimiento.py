"""Display recorded results only; never invoke evaluation or inference."""

import plotly.express as px
import streamlit as st

from comun import COLORES, NOMBRES_COMPLETOS, cargar_datos, paired_metrics, performance_visible

st.set_page_config(page_title="Rendimiento", page_icon="📊", layout="wide")
st.title("Rendimiento")
if not performance_visible():
    st.info("Rendimiento oculto. Active el control lateral para mostrarlo.")
    st.stop()

data = cargar_datos()
st.caption("Solo CSV existentes: no se ejecutan modelos ni se reevalúa el conjunto de prueba.")
for issue in data["issues"]:
    if not issue.startswith(("train.csv:", "splits.csv:")):
        st.warning(issue)
choice = st.sidebar.selectbox("Modelo", ["all", *NOMBRES_COMPLETOS],
                              format_func=lambda value: "Todos" if value == "all" else NOMBRES_COMPLETOS[value])
models = list(NOMBRES_COMPLETOS) if choice == "all" else [choice]
metrics = data["metricas"]
organs = sorted(metrics["organ"].unique())
chosen = st.sidebar.multiselect("Órganos", organs, default=organs)
filtered = metrics[metrics["organ"].isin(chosen)]
paired, excluded = paired_metrics(filtered, models)
style = dict(color="modelo", color_discrete_map=COLORES, category_orders={"modelo": list(NOMBRES_COMPLETOS)})
metric = st.selectbox("Métrica", ["dice", "iou"], format_func=str.upper)
st.caption("Dice e IoU: [0, 1], mayor es mejor. Medias por imagen, no métricas globales de píxeles.")
st.caption("No hay intervalos de confianza ni réplicas: la dispersión no mide incertidumbre estadística.")
if excluded:
    st.warning(f"{excluded} filas sin pareja excluidas: se compara la intersección de imágenes y órganos.")
if paired.empty:
    st.info("No hay métricas comunes para los modelos y órganos seleccionados.")
else:
    st.metric("Imágenes comunes en la evaluación registrada", paired["id"].nunique())
    summary = paired.groupby("modelo", as_index=False)[["dice", "iou"]].mean()
    st.plotly_chart(px.bar(summary, x="modelo", y=metric, range_y=[0, 1],
                           title="Comparación de modelos", **style), width="stretch")
    grouped = paired.groupby(["modelo", "organ"], as_index=False)[["dice", "iou"]].mean()
    st.plotly_chart(px.bar(grouped, x="organ", y=metric, barmode="group", range_y=[0, 1],
                           title="Comparación por órgano", **style), width="stretch")
    st.plotly_chart(px.box(paired, x="organ", y=metric, points="all", range_y=[0, 1],
                           title="Distribución por imagen", **style), width="stretch")
    failures = paired.groupby(["modelo", "organ"])[metric].agg(
        imágenes="size", media="mean", mínimo="min", desviación="std"
    ).reset_index()
    st.subheader("Patrones de menor rendimiento")
    st.dataframe(failures.sort_values("media"), hide_index=True, width="stretch")
    st.caption(
        "La tabla ordena medias por órgano, sin seleccionar imágenes. Compare cantidad y cobertura FTU "
        "en Exploración si esos metadatos están disponibles; no se atribuyen causas sin evidencia."
    )
    if {"segundos", "dispositivo"}.issubset(paired.columns):
        timing = paired.groupby(["modelo", "dispositivo"], as_index=False)["segundos"].mean()
        st.plotly_chart(px.bar(timing, x="modelo", y="segundos", hover_data=["dispositivo"],
                               title="Tiempo medio registrado (segundos)", **style), width="stretch")
        st.dataframe(timing, hide_index=True, width="stretch")
        st.caption("Dispositivo del CSV; no es un benchmark de este Mac ni incluye necesariamente todo el preprocesamiento.")

history = data["historial"]
history = history[history["modelo"].isin(models)].sort_values(["modelo", "epoca"])
experiments = data["experimentos"]
experiments = experiments[experiments["modelo"].isin(models)]
st.subheader("Entrenamiento y validación registrados")
st.caption("Las curvas son globales por modelo; el filtro de órgano no modifica el historial.")
if history.empty:
    st.info("No hay historial válido para los modelos seleccionados.")
else:
    for measure in ["dice", "loss"]:
        curves = history.melt(id_vars=["modelo", "epoca"], value_vars=[f"train_{measure}", f"val_{measure}"],
                              var_name="serie", value_name="valor")
        figure = px.line(curves, x="epoca", y="valor", line_dash="serie", markers=True,
                         title=f"Curvas de {measure}", **style)
        if measure == "dice":
            figure.update_yaxes(range=[0, 1])
        for row in experiments.itertuples():
            best = history[(history["modelo"] == row.modelo) & (history["epoca"] == row.mejor_epoca)]
            if not best.empty:
                figure.add_scatter(x=best["epoca"], y=best[f"val_{measure}"], mode="markers",
                                   marker=dict(size=13, symbol="diamond", color=COLORES[row.modelo]),
                                   name=f"{NOMBRES_COMPLETOS[row.modelo]} · mejor época")
        st.plotly_chart(figure, width="stretch")
if not experiments.empty:
    st.subheader("Mejor época según el registro de validación")
    columns = [column for column in ["modelo", "mejor_epoca", "mejor_val_dice", "epocas_ejecutadas", "estado"]
               if column in experiments]
    st.dataframe(experiments[columns], hide_index=True, width="stretch")
    st.caption("La mejor época viene de experimentos_modelos.csv; no se selecciona usando las métricas de prueba.")
