import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from io import BytesIO
import os

# =========================
# CONFIGURAÇÃO
# =========================

st.set_page_config(
    page_title="Dashboard Financeiro",
    page_icon="💰",
    layout="wide"
)

ARQUIVO = "movimentacoes.csv"

# =========================
# CRIA ARQUIVO
# =========================

if not os.path.exists(ARQUIVO):
    pd.DataFrame(
        columns=[
            "ID",
            "Data",
            "Descricao",
            "Valor",
            "Tipo",
            "Categoria"
        ]
    ).to_csv(ARQUIVO, index=False)

# =========================
# FUNÇÕES
# =========================

def carregar_dados():
    df = pd.read_csv(ARQUIVO)

    if not df.empty:
        df["Data"] = pd.to_datetime(df["Data"])

    return df


def salvar_dados(df):
    df.to_csv(ARQUIVO, index=False)

# =========================
# MENU
# =========================

menu = st.sidebar.selectbox(
    "Menu",
    [
        "Dashboard",
        "Cadastrar",
        "Editar / Excluir"
    ]
)

# =========================
# CADASTRAR
# =========================

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
            min_value=0.0,
            step=0.01
        )

        tipo = st.selectbox(
            "Tipo",
            ["Entrada", "Saída"]
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

        salvar = st.form_submit_button(
            "Salvar"
        )

        if salvar:

            df = carregar_dados()

            novo_id = 1

            if not df.empty:
                novo_id = int(df["ID"].max()) + 1

            novo = pd.DataFrame(
                [{
                    "ID": novo_id,
                    "Data": str(data),
                    "Descricao": descricao,
                    "Valor": valor,
                    "Tipo": tipo,
                    "Categoria": categoria
                }]
            )

            df = pd.concat(
                [df, novo],
                ignore_index=True
            )

            salvar_dados(df)

            st.success(
                "Movimentação cadastrada!"
            )

# =========================
# EDITAR / EXCLUIR
# =========================

elif menu == "Editar / Excluir":

    st.title("✏️ Editar ou Excluir")

    df = carregar_dados()

    if df.empty:
        st.warning("Nenhum registro encontrado.")
        st.stop()

    id_escolhido = st.selectbox(
        "Selecione o lançamento",
        df["ID"].tolist()
    )

    registro = df[
        df["ID"] == id_escolhido
    ].iloc[0]

    with st.form("editar"):

        nova_data = st.date_input(
            "Data",
            pd.to_datetime(
                registro["Data"]
            ).date()
        )

        nova_descricao = st.text_input(
            "Descrição",
            registro["Descricao"]
        )

        novo_valor = st.number_input(
            "Valor",
            value=float(
                registro["Valor"]
            )
        )

        novo_tipo = st.selectbox(
            "Tipo",
            ["Entrada", "Saída"],
            index=0 if registro["Tipo"] == "Entrada" else 1
        )

        nova_categoria = st.text_input
