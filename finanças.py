import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime
from io import BytesIO

# ==========================
# CONFIG
# ==========================

st.set_page_config(
    page_title="Dashboard Financeiro",
    page_icon="💰",
    layout="wide"
)

# ==========================
# BANCO
# ==========================

conn = sqlite3.connect(
    "financeiro.db",
    check_same_thread=False
)

cursor = conn.cursor()

cursor.execute("""
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

# ==========================
# FUNÇÕES
# ==========================

def carregar_dados():
    return pd.read_sql(
        "SELECT * FROM movimentacoes",
        conn
    )

def adicionar_movimento(
    data,
    descricao,
    valor,
    tipo,
    categoria
):
    cursor.execute("""
        INSERT INTO movimentacoes
        (data,descricao,valor,tipo,categoria)
        VALUES (?,?,?,?,?)
    """, (
        data,
        descricao,
        valor,
        tipo,
        categoria
    ))
    conn.commit()

def atualizar_movimento(
    id,
    data,
    descricao,
    valor,
    tipo,
    categoria
):
    cursor.execute("""
        UPDATE movimentacoes
        SET
        data=?,
        descricao=?,
        valor=?,
        tipo=?,
        categoria=?
        WHERE id=?
    """,(
        data,
        descricao,
        valor,
        tipo,
        categoria,
        id
    ))

    conn.commit()

def excluir_movimento(id):
    cursor.
