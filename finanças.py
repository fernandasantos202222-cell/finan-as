import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from io import BytesIO
import os

st.set_page_config(
    page_title="Dashboard Financeiro",
    page_icon="💰",
    layout="wide"
)

ARQUIVO = "movimentacoes.csv"

# =====================
# CRIA CSV SE NÃO EXISTIR
# =====================

if not os.path.exists(ARQUIVO):

    df_vazio = pd.DataFrame(
        columns=[
            "ID",
            "Data",
            "Descricao",
            "Valor",
            "Tipo",
            "Categoria"
        ]
    )

    df_vazio.to_csv(
        ARQUIVO,
        index=False
    )

# =====================
# FUNÇÕES
# =====================

def carregar():

    df = pd.read_csv(ARQUIVO)

    if not df.empty:
        df["Data"] = pd.to_datetime(df["Data"])

    return df


def salvar(df):

    df.to_csv(
        ARQUIVO,
        index=False
    )

# =====================
# MENU
# =====================

menu = st.sidebar.radio(
    "Menu",
    [
        "Dashboard",
        "Cadastrar",
        "Editar / Excluir"
    ]
)

# =====================
# CADASTRO
# =====================

if menu == "Cadastrar":

    st.title("➕ Nova Movimentação")

    with st.form("cadastro"):

        data = st.date_input(
            "Data",
            value=date.today()
        )

        descricao = st.text_input(
            "Descrição"
        )

        valor = st.number_input(
            "Valor",
            min_value=0.0
        )

        tipo =
