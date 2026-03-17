import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(layout="wide")

st.title("⚡ Dashboard de Gestão de Créditos - GD")

# Upload do arquivo
file = st.file_uploader("Upload da planilha de rateio", type=["xlsx"])

if file:
    df = pd.read_excel(file, sheet_name="Rateio_Proposto")

    # =========================
    # CÁLCULOS
    # =========================
    required_cols = ["novo_rateio", "saldo_atual", "consumo_medio", "UC"]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        st.error(
            "Colunas obrigatórias ausentes na planilha. Verifique a aba 'Rateio_Proposto'."
        )
        st.write("Colunas existentes:", list(df.columns))
        st.write("Colunas faltantes:", missing_cols)
        st.stop()

    GERACAO_MWH = 300
    # Garantir que consumo_medio não contenha zeros para evitar divisão por zero
    df["consumo_medio"] = df["consumo_medio"].replace(0, np.nan)

    df["energia_alocada"] = df["novo_rateio"] * GERACAO_MWH / 100
    df["saldo_pos"] = df["saldo_atual"] + df["energia_alocada"] - df["consumo_medio"]
    df["meses_pos"] = df["saldo_pos"] / df["consumo_medio"]

    # =========================
    # KPIs
    # =========================
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Saldo Total Antes (MWh)", round(df["saldo_atual"].sum(), 1))
    col2.metric("Saldo Total Depois (MWh)", round(df["saldo_pos"].sum(), 1))
    col3.metric("Cobertura Média Antes (meses)", round((df["saldo_atual"]/df["consumo_medio"]).mean(), 2))
    col4.metric("Cobertura Média Depois (meses)", round(df["meses_pos"].mean(), 2))

    st.divider()

    # =========================
    # DISTRIBUIÇÃO DE SALDO
    # =========================
    col1, col2 = st.columns(2)

    with col1:
        fig1 = px.histogram(
            df,
            x=df["saldo_atual"] / df["consumo_medio"],
            nbins=30,
            title="Distribuição de Meses de Saldo - Antes"
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        fig2 = px.histogram(
            df,
            x=df["meses_pos"],
            nbins=30,
            title="Distribuição de Meses de Saldo - Depois"
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # =========================
    # TOP RISCOS
    # =========================
    st.subheader("⚠️ UCs com menor saldo (Depois do rateio)")

    risco = df.sort_values("meses_pos").head(20)

    st.dataframe(
        risco[[
            "UC",
            "consumo_medio",
            "saldo_atual",
            "meses_pos"
        ]]
    )

    # =========================
    # VARIAÇÃO
    # =========================
    df["delta_meses"] = df["meses_pos"] - (df["saldo_atual"]/df["consumo_medio"])

    fig3 = px.scatter(
        df,
        x="saldo_atual",
        y="delta_meses",
        size="consumo_medio",
        title="Impacto do Rateio por UC",
        labels={
            "saldo_atual": "Saldo Atual (MWh)",
            "delta_meses": "Variação de Meses"
        }
    )

    st.plotly_chart(fig3, use_container_width=True)

    # =========================
    # CURVA DE EQUILÍBRIO
    # =========================
    st.subheader("📈 Curva de Cobertura do Portfólio")

    df_sorted = df.sort_values("meses_pos")

    fig4 = px.line(
        df_sorted,
        y="meses_pos",
        title="Cobertura por UC após rateio"
    )

    st.plotly_chart(fig4, use_container_width=True)
    