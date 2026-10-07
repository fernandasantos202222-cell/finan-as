import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from datetime import date
import os

# ============================
# CONFIGURAÇÃO
# ============================

st.set_page_config(
    page_title="Controle Financeiro",
    page_icon="💰",
    layout="wide"
)

ARQUIVO = "movimentacoes.csv"

# ============================
# CRIA CSV
# ============================

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

# ============================
# FUNÇÕES
# ============================

def carregar_dados():

    try:

        df = pd.read_csv(ARQUIVO)

        if df.empty:
            return df

        # Corrige datas inválidas
        df["Data"] = pd.to_datetime(
            df["Data"],
            errors="coerce"
        )

        # Remove registros ruins
        df = df.dropna(subset=["Data"])

        # Corrige número
        df["Valor"] = pd.to_numeric(
            df["Valor"],
            errors="coerce"
        ).fillna(0)

        df["ID"] = pd.to_numeric(
            df["ID"],
            errors="coerce"
        ).fillna(0).astype(int)

        return df

    except:
        return pd.DataFrame(
            columns=[
                "ID",
                "Data",
                "Descricao",
                "Valor",
                "Tipo",
                "Categoria"
            ]
        )


def salvar_dados(df):
    df.to_csv(ARQUIVO, index=False)

# ============================
# MENU
# ============================

menu = st.sidebar.radio(
    "Navegação",
    [
        "Dashboard",
        "Cadastrar",
        "Editar / Excluir"
    ]
)

# ============================
# CADASTRO
# ============================

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
                "Lazer",
                "Educação",
                "Investimento",
                "Outros"
            ]
        )

        btn = st.form_submit_button(
            "Salvar"
        )

        if btn:

            df = carregar_dados()

            novo_id = 1

            if not df.empty:
                novo_id = int(df["ID"].max()) + 1

            novo = pd.DataFrame([{
                "ID": novo_id,
                "Data": pd.Timestamp(data).strftime("%Y-%m-%d"),
                "Descricao": descricao,
                "Valor": valor,
                "Tipo": tipo,
                "Categoria": categoria
            }])

            df = pd.concat(
                [df, novo],
                ignore_index=True
            )

            salvar_dados(df)

            st.success(
                "Cadastro realizado!"
            )

# ============================
# EDITAR / EXCLUIR
# ============================

elif menu == "Editar / Excluir":

    st.title("✏️ Editar ou Excluir")

    df = carregar_dados()

    if df.empty:

        st.warning(
            "Nenhum lançamento encontrado."
        )

        st.stop()

    id_escolhido = st.selectbox(
        "Selecione o ID",
        df["ID"].tolist()
    )

    registro = df[
        df["ID"] == id_escolhido
    ].iloc[0]

    with st.form("edicao"):

        data = st.date_input(
            "Data",
            registro["Data"].date()
        )

        descricao = st.text_input(
            "Descrição",
            registro["Descricao"]
        )

        valor = st.number_input(
            "Valor",
            value=float(registro["Valor"])
        )

        tipo = st.selectbox(
            "Tipo",
            ["Entrada", "Saída"],
            index=0 if registro["Tipo"] == "Entrada" else 1
        )

        categoria = st.text_input(
            "Categoria",
            registro["Categoria"]
        )

        col1, col2 = st.columns(2)

        atualizar = col1.form_submit_button(
            "Atualizar"
        )

        excluir = col2.form_submit_button(
            "Excluir"
        )

        if atualizar:

            idx = df[
                df["ID"] == id_escolhido
            ].index[0]

            df.loc[idx, "Data"] = pd.Timestamp(
                data
            ).strftime("%Y-%m-%d")

            df.loc[idx, "Descricao"] = descricao
            df.loc[idx, "Valor"] = valor
            df.loc[idx, "Tipo"] = tipo
            df.loc[idx, "Categoria"] = categoria

            salvar_dados(df)

            st.success(
                "Atualizado com sucesso!"
            )

        if excluir:

            df = df[
                df["ID"] != id_escolhido
            ]

            salvar_dados(df)

            st.success(
                "Registro removido!"
            )

# ============================
# DASHBOARD
# ============================

else:

    st.title("📊 Dashboard Financeiro")

    df = carregar_dados()

    if df.empty:

        st.warning(
            "Cadastre movimentações."
        )

        st.stop()

    data_min = df["Data"].min()
    data_max = df["Data"].max()

    col1, col2 = st.columns(2)

    with col1:

        data_inicio = st.date_input(
            "Data Inicial",
            value=data_min.date()
        )

    with col2:

        data_fim = st.date_input(
            "Data Final",
            value=data_max.date()
        )

    df = df[
        (df["Data"] >= pd.Timestamp(data_inicio))
        &
        (df["Data"] <= pd.Timestamp(data_fim))
    ]

    entradas = df[
        df["Tipo"] == "Entrada"
    ]["Valor"].sum()

    saidas = df[
        df["Tipo"] == "Saída"
    ]["Valor"].sum()

    saldo = entradas - saidas

    media_gasto = df[
        df["Tipo"] == "Saída"
    ]["Valor"].mean()

    if pd.isna(media_gasto):
        media_gasto = 0

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Saldo",
        f"R$ {saldo:,.2f}"
    )

    c2.metric(
        "Entradas",
        f"R$ {entradas:,.2f}"
    )

    c3.metric(
        "Saídas",
        f"R$ {saidas:,.2f}"
    )

    c4.metric(
        "Gasto Médio",
        f"R$ {media_gasto:,.2f}"
    )

    # Evolução

    st.subheader("📈 Evolução Mensal")

    df["Movimento"] = df.apply(
        lambda x:
        x["Valor"]
        if x["Tipo"] == "Entrada"
        else -x["Valor"],
        axis=1
    )

    df["Mes"] = df["Data"].dt.strftime(
        "%Y-%m"
    )

    evolucao = (
        df.groupby("Mes")["Movimento"]
        .sum()
        .reset_index()
    )

    fig = px.line(
        evolucao
