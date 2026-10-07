import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import os

# ==========================
# CONFIGURAÇÃO
# ==========================

st.set_page_config(
    page_title="Controle Financeiro",
    page_icon="💰",
    layout="wide"
)

ARQUIVO = "financeiro.csv"

# ==========================
# CRIAR CSV SE NÃO EXISTIR
# ==========================

if not os.path.exists(ARQUIVO):

    df = pd.DataFrame(
        columns=[
            "Data",
            "Descricao",
            "Valor",
            "Tipo",
            "Categoria"
        ]
    )

    df.to_csv(
        ARQUIVO,
        index=False
    )

# ==========================
# FUNÇÕES
# ==========================

def carregar_dados():

    df = pd.read_csv(ARQUIVO)

    if not df.empty:

        df["Data"] = pd.to_datetime(
            df["Data"],
            errors="coerce"
        )

        df = df.dropna(
            subset=["Data"]
        )

    return df


def salvar_dados(df):

    df.to_csv(
        ARQUIVO,
        index=False
    )

# ==========================
# MENU
# ==========================

pagina = st.sidebar.selectbox(
    "Menu",
    [
        "Dashboard",
        "Lançamentos"
    ]
)

# ==========================
# LANÇAMENTOS
# ==========================

if pagina == "Lançamentos":

    st.title("💵 Lançamentos")

    df = carregar_dados()

    st.subheader("Novo lançamento")

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

        tipo = st.radio(
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
                "Investimento",
                "Outros"
            ]
        )

    if st.button(
        "Salvar lançamento",
        use_container_width=True
    ):

        if descricao.strip() == "":
            st.error(
                "Informe a descrição."
            )

        else:

            novo = pd.DataFrame(
                [{
                    "Data": data.strftime("%Y-%m-%d"),
                    "Descricao": descricao,
                    "Valor": float(valor),
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
                "Lançamento salvo com sucesso."
            )

            st.rerun()

    st.divider()

    st.subheader(
        "Editar ou excluir"
    )

    if not df.empty:

        df_editado = st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic"
        )

        if st.button(
            "Salvar alterações"
        ):

            salvar_dados(df_editado)

            st.success(
                "Alterações salvas."
            )

            st.rerun()

# ==========================
# DASHBOARD
# ==========================

else:

    st.title(
        "📊 Dashboard Financeiro"
    )

    df = carregar_dados()

    if df.empty:

        st.info(
            "Cadastre lançamentos para visualizar os indicadores."
        )

        st.stop()

    menor_data = df["Data"].min()
    maior_data = df["Data"].max()

    col1, col2 = st.columns(2)

    with col1:

        data_inicio = st.date_input(
            "Data Inicial",
            value=menor_data.date()
        )

    with col2:

        data_fim = st.date_input(
            "Data Final",
            value=maior_data.date()
        )

    filtro = (
        (df["Data"] >= pd.Timestamp(data_inicio))
        &
        (df["Data"] <= pd.Timestamp(data_fim))
    )

    df_filtrado = df[filtro]

    entradas = df_filtrado[
        df_filtrado["Tipo"] == "Entrada"
    ]["Valor"].sum()

    saidas = df_filtrado[
        df_filtrado["Tipo"] == "Saída"
    ]["Valor"].sum()

    saldo = entradas - saidas

    gasto_medio = df_filtrado[
        df_filtrado["Tipo"] == "Saída"
    ]["Valor"].mean()

    if pd.isna(gasto_medio):
        gasto_medio = 0

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
        f"R$ {gasto_medio:,.2f}"
    )

    # Evolução

    df_plot = df_filtrado.copy()

    df_plot["Movimento"] = df_plot.apply(
        lambda linha:
        linha["Valor"]
        if linha["Tipo"] == "Entrada"
        else -linha["Valor"],
        axis=1
    )

    df_plot["Mes"] = (
        df_plot["Data"]
        .dt.to_period("M")
        .astype(str)
    )

    evolucao = (
        df_plot.groupby("Mes")["Movimento"]
        .sum()
        .reset_index()
    )

    st.subheader(
        "📈 Evolução Mensal"
    )

    fig1 = px.line(
        evolucao,
        x="Mes",
        y="Movimento",
        markers=True
    )

    st.plotly_chart(
        fig1,
        use_container_width=True
    )

    # Categorias

    categorias = (
        df_filtrado[
            df_filtrado["Tipo"] == "Saída"
        ]
        .groupby("Categoria")["Valor"]
        .sum()
        .reset_index()
    )

    if not categorias.empty:

        st.subheader(
            "🥧 Despesas por Categoria"
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
        "📋 Movimentações"
    )

    st.dataframe(
        df_filtrado,
        use_container_width=True
    )

    # Excel

    output = BytesIO()

    resumo = pd.DataFrame(
        {
            "Indicador": [
                "Entradas",
                "Saídas",
                "Saldo",
                "Gasto Médio"
            ],
            "Valor": [
                entradas,
                saidas,
                saldo,
                gasto_medio
            ]
        }
    )

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        df_filtrado.to_excel(
            writer,
            sheet_name="Movimentacoes",
            index=False
        )

        resumo.to_excel(
            writer,
            sheet_name="Resumo",
            index=False
        )

        categorias.to_excel(
            writer,
            sheet_name="Categorias",
            index=False
        )

    st.download_button(
        "📥 Baixar Excel",
        output.getvalue(),
        file_name="relatorio_financeiro.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
