import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import os

# ----------------------------------
# CONFIG
# ----------------------------------

st.set_page_config(
    page_title="Dashboard Financeiro",
    page_icon="💰",
    layout="wide"
)

ARQUIVO = "financeiro.csv"

# ----------------------------------
# CRIAR CSV
# ----------------------------------

if not os.path.exists(ARQUIVO):

    pd.DataFrame(
        columns=[
            "Data",
            "Descrição",
            "Valor",
            "Tipo",
            "Categoria"
        ]
    ).to_csv(
        ARQUIVO,
        index=False
    )

# ----------------------------------
# CARREGAR
# ----------------------------------

@st.cache_data
def carregar():

    df = pd.read_csv(ARQUIVO)

    if not df.empty:

        df["Data"] = pd.to_datetime(
            df["Data"],
            errors="coerce"
        )

        df = df.dropna(subset=["Data"])

    return df

# ----------------------------------
# SALVAR
# ----------------------------------

def salvar(df):

    df.to_csv(
        ARQUIVO,
        index=False
    )

    carregar.clear()

# ----------------------------------
# MENU
# ----------------------------------

menu = st.sidebar.radio(
    "Menu",
    [
        "Dashboard",
        "Lançamentos"
    ]
)

# ==================================
# LANÇAMENTOS
# ==================================

if menu == "Lançamentos":

    st.title("💵 Lançamentos")

    with st.expander(
        "➕ Novo Lançamento",
        expanded=True
    ):

        col1, col2 = st.columns(2)

        with col1:

            data = st.date_input("Data")

            descricao = st.text_input(
                "Descrição"
            )

            valor = st.number_input(
                "Valor",
                min_value=0.01,
                step=0.01
            )

        with col2:

            tipo = st.selectbox(
                "Tipo",
                [
                    "Entrada",
                    "Saída"
                ]
            )

            categoria = st.selectbox(
                "Categoria",
                [
                    "Salário",
                    "Moradia",
                    "Alimentação",
                    "Transporte",
                    "Saúde",
                    "Educação",
                    "Lazer",
                    "Investimentos",
                    "Outros"
                ]
            )

        if st.button(
            "💾 Salvar Lançamento",
            use_container_width=True
        ):

            df = carregar()

            novo = pd.DataFrame([
                {
                    "Data": data,
                    "Descrição": descricao,
                    "Valor": valor,
                    "Tipo": tipo,
                    "Categoria": categoria
                }
            ])

            df = pd.concat(
                [df, novo],
                ignore_index=True
            )

            salvar(df)

            st.success(
                "Lançamento salvo!"
            )

            st.rerun()

    st.divider()

    st.subheader(
        "✏️ Editar ou Excluir"
    )

    df = carregar()

    editado = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True
    )

    if st.button(
        "Salvar Alterações"
    ):

        salvar(editado)

        st.success(
            "Alterações salvas!"
        )

# ==================================
# DASHBOARD
# ==================================

else:

    st.title("📊 Dashboard Financeiro")

    df = carregar()

    if df.empty:

        st.info(
            "Cadastre lançamentos."
        )

        st.stop()

    # FILTRO

    col1, col2 = st.columns(2)

    with col1:

        inicio
