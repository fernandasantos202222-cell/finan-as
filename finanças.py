import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import os
from datetime import date

st.set_page_config(
    page_title="Dashboard Financeiro",
    page_icon="💰",
    layout="wide"
)

ARQUIVO = "movimentacoes.csv"

# ------------------------
# CRIAR CSV
# ------------------------

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


# ------------------------
# FUNCOES
# ------------------------

def carregar_dados():

    try:

        df = pd.read_csv(ARQUIVO)

        if df.empty:
            return df

        df["Data"] = pd.to_datetime(
            df["Data"],
            errors="coerce"
        )

        df = df.dropna(subset=["Data"])

        df["Valor"] = pd.to_numeric(
            df["Valor"],
            errors="coerce"
        ).fillna(0)

        return df

    except Exception:

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


# ------------------------
# MENU
# ------------------------

pagina = st.sidebar.radio(
    "Menu",
    [
        "Dashboard",
        "Cadastrar",
        "Editar / Excluir"
    ]
)

# ------------------------
# CADASTRO
# ------------------------

if pagina == "Cadastrar":

    st.title("➕ Cadastro")

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
                "Lazer",
                "Educação",
                "Investimentos",
                "Outros"
            ]
        )

        enviar = st.form_submit_button(
            "Salvar"
        )

        if enviar:

            df = carregar_dados()

            novo_id = 1

            if not df.empty:
                novo_id = int(
                    df["ID"].max()
                ) + 1

            novo = pd.DataFrame([
                {
                    "ID": novo_id,
                    "Data": data.strftime("%Y-%m-%d"),
                    "Descricao": descricao,
                    "Valor": valor,
                    "Tipo": tipo,
                    "Categoria": categoria
                }
            ])

            df = pd.concat(
                [df, novo],
                ignore_index=True
            )

            salvar_dados(df)

            st.success(
                "Registro salvo!"
            )

# ------------------------
# EDITAR
# ------------------------

elif pagina == "Editar / Excluir":

    st.title("✏️ Editar / Excluir")

    df = carregar_dados()

    if df.empty:
        st.warning("Nenhum registro.")
        st.stop()

    id_escolhido = st.selectbox(
        "Selecione",
        df["ID"]
    )

    reg = df[
        df["ID"] == id_escolhido
    ].iloc[0]

    with st.form("editar"):

        data = st.date_input(
            "Data",
            reg["Data"].date()
        )

        descricao = st.text_input(
            "Descrição",
            reg["Descricao"]
        )

        valor = st.number_input(
            "Valor",
            value=float(reg["Valor"])
        )

        tipo = st.selectbox(
            "Tipo",
            ["Entrada", "Saída"],
            index=0 if reg["Tipo"] == "Entrada" else 1
        )

        categoria = st.text_input(
            "Categoria",
            reg["Categoria"]
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

            df.loc[idx, "Data"] = data.strftime("%Y-%m-%d")
            df.loc[idx, "Descricao"] = descricao
            df.loc[idx, "Valor"] = valor
            df.loc[idx, "Tipo"] = tipo
            df.loc[idx, "Categoria"] = categoria

            salvar_dados(df)

            st.success(
                "Atualizado!"
            )

        if excluir:

            df = df[
                df["ID"] != id_escolhido
            ]

            salvar_dados(df)

            st.success(
                "Removido!"
            )

# ------------------------
# DASHBOARD
# ------------------------

else:

    st.title("📊 Dashboard Financeiro")

    df = carregar_dados()

    if df.empty:

        st.warning(
            "Cadastre movimentações."
        )

        st.stop()

    data_inicio = st.date_input(
        "Data Inicial",
        value=df["Data"].min().date()
    )

    data_fim = st.date_input(
        "Data Final",
        value=df["Data"].max().date()
    )

    df = df[
        (df["Data"] >= pd.Timestamp(data_inicio))
        &
        (df["Data"] <= pd.Timestamp(data_fim))
    ]

    entradas = (
        df[df["Tipo"] == "Entrada"]["Valor"]
        .sum()
    )

    saidas = (
        df[df["Tipo"] == "Saída"]["Valor"]
        .sum()
    )

    saldo = entradas - saidas

    media = (
        df[df["Tipo"] == "Saída"]["Valor"]
        .mean()
    )

    if pd.isna(media):
        media = 0

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
        "Média",
        f"R$ {media:,.2f}"
    )

    # Evolução

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

    st.subheader(
        "📈 Evolução Mensal"
    )

    fig = px.line(
        evolucao,
        x="Mes",
        y="Movimento",
        markers=True
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # Categorias

    categorias = (
        df[df["Tipo"] == "Saída"]
        .groupby("Categoria")["Valor"]
        .sum()
        .reset_index()
    )

    if not categorias.empty:

        st.subheader(
            "🥧 Gastos por Categoria"
        )

        fig2 = px.pie(
            categorias,
            names="Categoria",
            values="Valor"
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

    st.subheader(
        "📋 Lançamentos"
    )

    st.dataframe
