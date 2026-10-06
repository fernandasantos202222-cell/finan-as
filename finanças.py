import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import date

# =========================
# CONFIGURAÇÃO
# =========================

st.set_page_config(
    page_title="Dashboard Financeiro",
    page_icon="💰",
    layout="wide"
)

# =========================
# BANCO SQLITE
# =========================

conn = sqlite3.connect("financeiro.db", check_same_thread=False)

conn.execute("""
CREATE TABLE IF NOT EXISTS movimentacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT,
    descricao TEXT,
    valor REAL,
    tipo TEXT,
    categoria TEXT
)
""")

conn.commit()

# =========================
# FUNÇÕES
# =========================

def carregar_dados():
    return pd.read_sql(
        "SELECT * FROM movimentacoes",
        conn,
        parse_dates=["data"]
    )

def adicionar_movimento(data, descricao, valor, tipo, categoria):
    conn.execute("""
        INSERT INTO movimentacoes
        (data, descricao, valor, tipo, categoria)
        VALUES (?, ?, ?, ?, ?)
    """, (data, descricao, valor, tipo, categoria))

    conn.commit()

# =========================
# MENU
# =========================

st.sidebar.title("💰 Financeiro")

pagina = st.sidebar.radio(
    "Menu",
    [
        "Dashboard",
        "Nova Movimentação",
        "Histórico"
    ]
)

# =========================
# NOVA MOVIMENTAÇÃO
# =========================

if pagina == "Nova Movimentação":

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

            adicionar_movimento(
                str(data),
                descricao,
                valor,
                tipo,
                categoria
            )

            st.success("Movimentação cadastrada!")

# =========================
# HISTÓRICO
# =========================

elif pagina == "Histórico":

    st.title("📋 Histórico")

    df = carregar_dados()

    if len(df) > 0:

        st.dataframe(
            df.sort_values(
                "data",
                ascending=False
            ),
            use_container_width=True
        )

        csv = df.to_csv(index=False)

        st.download_button(
            "⬇️ Exportar CSV",
            csv,
            file_name="financeiro.csv",
            mime="text/csv"
        )

    else:

        st.info("Nenhum lançamento encontrado.")

# =========================
# DASHBOARD
# =========================

else:

    st.title("📊 Dashboard Financeiro")

    df = carregar_dados()

    if len(df) == 0:

        st.warning(
            "Cadastre movimentações para visualizar o dashboard."
        )

        st.stop()

    # Filtro período

    st.subheader("Filtro")

    col1, col2 = st.columns(2)

    with col1:
        data_inicio = st.date_input(
            "Data Inicial",
            value=df["data"].min().date()
        )

    with col2:
        data_fim = st.date_input(
            "Data Final",
            value=df["data"].max().date()
        )

    df = df[
        (df["data"] >= pd.Timestamp(data_inicio))
        &
        (df["data"] <= pd.Timestamp(data_fim))
    ]

    entradas = df[
        df["tipo"] == "Entrada"
    ]["valor"].sum()

    saidas = df[
        df["tipo"] == "Saída"
    ]["valor"].sum()

    saldo = entradas - saidas

    gasto_medio = 0

    if len(df) > 0:
        gasto_medio = (
            df[
                df["tipo"] == "Saída"
            ]["valor"].mean()
        )

    # CARDS

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

    # =====================
    # EVOLUÇÃO MENSAL
    # =====================

    st.subheader("📈 Evolução Mensal")

    df["mes"] = df["data"].dt.strftime(
        "%Y-%m"
    )

    df["valor_corrigido"] = df.apply(
        lambda x:
        x["valor"]
        if x["tipo"] == "Entrada"
        else -x["valor"],
        axis=1
    )

    mensal = (
        df.groupby("mes")["valor_corrigido"]
        .sum()
        .reset_index()
    )

    grafico_linha = px.line(
        mensal,
        x="mes",
        y="valor_corrigido",
        markers=True,
        title="Saldo por Mês"
    )

    st.plotly_chart(
        grafico_linha,
        use_container_width=True
    )

    # =====================
    # CATEGORIAS
    # =====================

    st.subheader(
        "🥧 Despesas por Categoria"
    )

    categorias = (
        df[df["tipo"] == "Saída"]
        .groupby("categoria")["valor"]
        .sum()
        .reset_index()
    )

    if len(categorias):

        grafico_pizza = px.pie(
            categorias,
            names="categoria",
            values="valor"
        )

        st.plotly_chart(
            grafico_pizza,
            use_container_width=True
        )

    # =====================
    # RESUMO MENSAL
    # =====================

    st.subheader("📅 Resumo Mensal")

    resumo = (
        df.groupby(
            [
                "mes",
                "tipo"
            ]
        )["valor"]
        .sum()
        .reset_index()
    )

    grafico_barra = px.bar(
        resumo,
        x="mes",
        y="valor",
        color="tipo",
        barmode="group"
    )

    st.plotly_chart(
        grafico_barra,
        use_container_width=True
    )

    # =====================
    # TABELA
    # =====================

    st.subheader("🧾 Últimos Lançamentos")

    st.dataframe(
        df.sort_values(
            "data",
            ascending=False
        ),
        use_container_width=True
    )
