"""Genera las figuras del informe a partir de data/train.csv."""

import os

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

sns.set_theme(style="whitegrid")

DATA = "data/train.csv"
OUT = "informe/figuras/"
os.makedirs(OUT, exist_ok=True)

train = pd.read_csv(DATA)
for col in ["organ", "data_source", "sex"]:
    train[col] = train[col].astype("category")


def rle_area(rle_string):
    return int(np.asarray(rle_string.split()[1::2], dtype=int).sum())


train["mask_px"] = train["rle"].map(rle_area)
train["mask_frac"] = train["mask_px"] / (train["img_height"] * train["img_width"])

orden_organ = train["organ"].value_counts().index


def guardar(nombre):
    plt.tight_layout()
    plt.savefig(OUT + nombre, dpi=150, bbox_inches="tight")
    plt.close()
    print("escrito", OUT + nombre)


# --- univariadas -----------------------------------------------------------
num_cols = ["age", "img_height", "mask_frac"]
titulos = ["Edad del donante", "Alto de la imagen (px)", "Proporción de FTU"]

fig, axes = plt.subplots(2, 3, figsize=(15, 7.5))
for i, (col, titulo) in enumerate(zip(num_cols, titulos)):
    sns.histplot(train[col], bins=25, ax=axes[0, i], color="#4C72B0")
    axes[0, i].set_title(titulo)
    axes[0, i].set_xlabel("")
    sns.boxplot(x=train[col], ax=axes[1, i], color="#4C72B0")
    axes[1, i].set_xlabel(titulo)
guardar("univariadas.png")

# --- categoricas -----------------------------------------------------------
fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
for ax, col in zip(axes, ["organ", "sex", "data_source"]):
    sns.countplot(data=train, x=col, order=train[col].value_counts().index,
                  ax=ax, hue=col, legend=False, palette="deep")
    ax.set_title(f"Frecuencia de {col}")
    ax.set_xlabel("")
    ax.tick_params(axis="x", rotation=30)
guardar("categoricas.png")

# --- cruces ----------------------------------------------------------------
fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))
sns.boxplot(data=train, x="organ", y="mask_frac", order=orden_organ, ax=axes[0],
            hue="organ", legend=False, palette="deep")
axes[0].set_title("Proporción de FTU por órgano")
axes[0].set_xlabel("")
axes[0].tick_params(axis="x", rotation=30)

sns.boxplot(data=train, x="organ", y="age", order=orden_organ, ax=axes[1],
            hue="organ", legend=False, palette="deep")
axes[1].set_title("Edad del donante por órgano")
axes[1].set_xlabel("")
axes[1].tick_params(axis="x", rotation=30)

tabla = pd.crosstab(train["organ"], train["sex"], normalize="index").loc[orden_organ]
tabla.plot(kind="bar", stacked=True, ax=axes[2], colormap="Set2")
axes[2].set_title("Composición por sexo dentro de cada órgano")
axes[2].set_xlabel("")
axes[2].set_ylabel("proporción")
axes[2].tick_params(axis="x", rotation=30)
guardar("cruces.png")

# --- dispersion ------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
sns.scatterplot(data=train, x="age", y="mask_frac", hue="organ", ax=axes[0],
                palette="deep", alpha=0.8, s=45)
axes[0].set_title("Edad vs. proporción de FTU")
axes[0].set_xlabel("edad (años)")
axes[0].set_ylabel("proporción de FTU")
axes[0].legend(title="órgano", fontsize=8)

sns.scatterplot(data=train, x="img_height", y="mask_frac", hue="organ", ax=axes[1],
                palette="deep", alpha=0.8, s=45, legend=False)
axes[1].set_title("Alto de la imagen vs. proporción de FTU")
axes[1].set_xlabel("alto de la imagen (px)")
axes[1].set_ylabel("")
guardar("dispersion.png")

# --- paradoja de Simpson (figura para la presentacion) ---------------------
fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)

sns.regplot(data=train, x="age", y="mask_frac", ax=axes[0], scatter_kws={"alpha": 0.55, "s": 35},
            line_kws={"color": "crimson", "lw": 2.5}, ci=None, color="#555555")
r_global = train["age"].corr(train["mask_frac"])
axes[0].set_title(f"Todos los órganos juntos:  r = {r_global:.3f}")
axes[0].set_xlabel("edad (años)")
axes[0].set_ylabel("proporción de FTU")

for organo, grupo in train.groupby("organ", observed=True):
    sns.regplot(data=grupo, x="age", y="mask_frac", ax=axes[1], ci=None,
                scatter_kws={"alpha": 0.55, "s": 35}, line_kws={"lw": 2.2}, label=organo)
axes[1].set_title("Separado por órgano: la tendencia se aplana o se invierte")
axes[1].set_xlabel("edad (años)")
axes[1].set_ylabel("")
axes[1].legend(title="órgano", fontsize=8)
guardar("simpson.png")


# --- proporcion de FTU por organo, version para diapositiva -----------------
plt.figure(figsize=(9, 5))
sns.boxplot(data=train, x="organ", y="mask_frac", order=orden_organ,
            hue="organ", legend=False, palette="deep")
plt.title("La FTU no ocupa lo mismo en cada órgano")
plt.xlabel("")
plt.ylabel("proporción de la imagen ocupada por la FTU")
guardar("ftu_por_organo.png")


# --- numeros que se citan en el informe -----------------------------------
print("\ncorr global age~mask_frac:", round(train["age"].corr(train["mask_frac"]), 3))
for organo, grupo in train.groupby("organ", observed=True):
    print(f"  {organo:15s} r = {grupo['age'].corr(grupo['mask_frac']):.3f}")
