import os

import matplotlib.pyplot as plt
import pandas as pd
import requests
import streamlit as st

API_URL = os.environ.get(
    "API_URL", "https://azmb4sby0e.execute-api.us-east-1.amazonaws.com/distritos"
)

st.set_page_config(page_title="Vulnerabilidad en Madrid 2024", layout="wide")


@st.cache_data(ttl=300)
def cargar():
    r = requests.get(API_URL, timeout=30)
    r.raise_for_status()
    df = pd.DataFrame(r.json())
    for c in df.columns:
        if c != "distrito":
            df[c] = pd.to_numeric(df[c])
    return df


def barras(df, col, media, etiqueta):
    d = df.sort_values(col)
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.barh(d["distrito"], d[col], color="#c0392b")
    ax.axvline(d[media].iloc[0], color="black", linestyle="--", label="Media ciudad")
    ax.set_xlabel(etiqueta)
    ax.legend()
    return fig


def dispersion(df, x, y, etiq_x, etiq_y):
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(df[x], df[y], color="#2980b9")
    for _, f in df.iterrows():
        ax.annotate(f["distrito"], (f[x], f[y]), fontsize=7)
    ax.set_xlabel(etiq_x)
    ax.set_ylabel(etiq_y)
    return fig


def resumen(df, x, y, rank_x, rank_y):
    c1, c2, c3 = st.columns(3)
    c1.metric("Pearson", round(df[x].corr(df[y]), 2))
    c2.metric("Spearman", round(df[rank_x].corr(df[rank_y]), 2))
    top5 = int(((df[rank_x] <= 5) & (df[rank_y] <= 5)).sum())
    c3.metric("Coinciden en el top 5", top5)


df = cargar()

st.title("Vulnerabilidad territorial en los distritos de Madrid, 2024")
st.caption("Índice IGUALA: un valor más alto equivale a mayor vulnerabilidad.")

pregunta = st.sidebar.radio(
    "Pregunta",
    [
        "1. Economía y empleo",
        "2. Población vs. economía",
        "3. Economía vs. bienestar",
        "4. Educación y cultura",
        "5. Educación vs. bienestar",
    ],
)

if pregunta.startswith("1"):
    st.subheader("Distritos por vulnerabilidad en economía y empleo")
    st.pyplot(barras(df, "ivt_ee", "ivt_ee_media_ciudad", "Índice economía y empleo"))
    st.dataframe(df.sort_values("rank_ee")[["rank_ee", "distrito", "ivt_ee", "ivt_ee_media_ciudad"]], hide_index=True)

elif pregunta.startswith("2"):
    st.subheader("¿Los distritos más poblados son los más vulnerables en economía?")
    st.pyplot(dispersion(df, "poblacion", "ivt_ee", "Población", "Índice economía y empleo"))
    resumen(df, "poblacion", "ivt_ee", "rank_poblacion", "rank_ee")
    st.dataframe(df.sort_values("rank_poblacion")[["rank_poblacion", "distrito", "poblacion", "rank_ee", "ivt_ee"]], hide_index=True)

elif pregunta.startswith("3"):
    st.subheader("¿Economía y bienestar coinciden?")
    st.pyplot(dispersion(df, "ivt_ee", "ivt_bi", "Índice economía y empleo", "Índice bienestar e igualdad"))
    resumen(df, "ivt_ee", "ivt_bi", "rank_ee", "rank_bi")
    st.dataframe(df.sort_values("rank_ee")[["distrito", "rank_ee", "ivt_ee", "rank_bi", "ivt_bi"]], hide_index=True)

elif pregunta.startswith("4"):
    st.subheader("Distritos por vulnerabilidad en educación y cultura")
    st.pyplot(barras(df, "ivt_ec", "ivt_ec_media_ciudad", "Índice educación y cultura"))
    st.dataframe(df.sort_values("rank_ec")[["rank_ec", "distrito", "ivt_ec", "ivt_ec_media_ciudad"]], hide_index=True)

else:
    st.subheader("¿Educación y bienestar coinciden?")
    st.pyplot(dispersion(df, "ivt_ec", "ivt_bi", "Índice educación y cultura", "Índice bienestar e igualdad"))
    resumen(df, "ivt_ec", "ivt_bi", "rank_ec", "rank_bi")
    st.dataframe(df.sort_values("rank_ec")[["distrito", "rank_ec", "ivt_ec", "rank_bi", "ivt_bi"]], hide_index=True)