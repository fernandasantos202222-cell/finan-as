*Cria 2 arquivos no GitHub:*

### 1 - `requirements.txt`
streamlit
pandas
plotly
openpyxl
fpdf2
libsql-experimental
### 2 - `app.py` - COPIA TUDO:
import streamlit as st
import pandas as pd
from datetime import date, timedelta
import io
import plotly.express as px
import plotly.graph_objects as go

# ============ BANCO TURSO + SQLITE FALLBACK ============
try:
    import libsql
    URL = str(st.secrets["TURSO_URL"]).strip().replace("\n","").replace("\r","").replace(" ","")
    RAW = str(st.secrets["TURSO_TOKEN"])
    TOKEN = "".join(RAW.split()).strip('"').strip("'")
    @st.cache_resource
    def get_conn():
        c = libsql.connect(database=URL, auth_token=TOKEN)
        c.execute("""CREATE TABLE IF NOT EXISTS financas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT, item TEXT, valor REAL, tipo TEXT, classe TEXT)""")
        c.commit()
        return c
    conn = get_conn()
except Exception as e:
    st.toast(f"Usando banco local: {e}")
    import sqlite3
    conn = sqlite3.connect("financas.db", check_same_thread=False)
    conn.execute("""CREATE TABLE IF NOT EXISTS financas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT, item TEXT, valor REAL, tipo TEXT, classe TEXT)""")
    conn.commit()

cur = conn.cursor()
def query_df():
    cur.execute("SELECT id, data, item, valor, tipo, classe FROM financas ORDER BY data DESC, id DESC")
    cols = [d[0] for d in cur.description] if cur.description else []
    return pd.DataFrame(cur.fetchall(), columns=cols)

def add_item(data, item, valor, tipo, classe):
    cur.execute("INSERT INTO financas (data, item, valor, tipo, classe) VALUES (?,?,?,?,?)",
                (str(data), item, float(valor), tipo, classe))
    conn.commit()
    return cur.lastrowid

def update_item(id_, data, item, valor, tipo, classe):
    cur.execute("UPDATE financas SET data=?, item=?, valor=?, tipo=?, classe=? WHERE id=?",
                (str(data), item, float(valor), tipo, classe, int(id_)))
    conn.commit()

def delete_item(id_):
    cur.execute("DELETE FROM financas WHERE id=?", (int(id_),))
    conn.commit()

# ============ APP ============
st.set_page_config(page_title="Finanças", layout="wide")
st.title("💰 Controle Financeiro")

if "edit_id" not in st.session_state: st.session_state.edit_id = None
menu = st.sidebar.radio("Menu", ["Dashboard", "Lançar", "Histórico / Editar / Deletar", "Resumo Excel"], index=0)

df = query_df()

# ============ DASHBOARD ============
if menu == "Dashboard":
    if df.empty:
        st.info("Nenhum lançamento ainda. Vai em Lançar")
    else:
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
        df['data'] = pd.to_datetime(df['data'], errors='coerce')
        df = df.dropna(subset=['data'])

        entradas = df[df['tipo']=='Entrada']['valor'].sum()
        saidas = df[df['tipo']=='Saida']['valor'].sum()
        saldo = entradas - saidas
        economia_pct = (saldo/entradas*100) if entradas>0 else 0
        media_gasto = df[df['tipo']=='Saida']['valor'].mean()

        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("💵 Entrada", f"R$ {entradas:,.2f}")
        c2.metric("💸 Saída", f"R$ {saidas:,.2f}")
        c3.metric("💰 Saldo", f"R$ {saldo:,.2f}")
        c4.metric("📊 Economia", f"{economia_pct:.1f}%")
        c5.metric("📉 Média Gasto", f"R$ {media_gasto:,.2f}")

        st.divider()
        # Evolução mensal
        df['mes'] = df['data'].dt.to_period('M').dt.to_timestamp()
        evo = df.groupby(['mes','tipo'])['valor'].sum().reset_index().sort_values('mes')
        fig_evo = px.line(evo, x='mes', y='valor', color='tipo', markers=True, title="Evolução Mensal - Entrada x Saída")
        st.plotly_chart(fig_evo, use_container_width=True, key="evo")

        c1,c2 = st.columns(2)
        # Por classe
        df_saida_classe = df[df['tipo']=='Saida'].groupby('classe')['valor'].sum().reset_index()
        if not df_saida_classe.empty:
            fig_classe = px.pie(df_saida_classe, values='valor', names='classe', title="Gastos por Classe")
            c1.plotly_chart(fig_classe, use_container_width=True, key="classe_pie")

        # Saldo acumulado
        df_saldo = df.sort_values('data').copy()
        df_saldo['entr'] = df_saldo.apply(lambda r: r['valor'] if r['tipo']=='Entrada' else 0, axis=1)
        df_saldo['sai'] = df_saldo.apply(lambda r: r['valor'] if r['tipo']=='Saida' else 0, axis=1)
        df_saldo['saldo_acum'] = (df_saldo['entr'] - df_saldo['sai']).cumsum()
        fig_saldo = px.area(df_saldo, x='data', y='saldo_acum', title="Saldo Acumulado")
        c2.plotly_chart(fig_saldo, use_container_width=True, key="saldo_acum")

        # Projeção futura - média últimos 3 meses
        st.subheader("🔮 Projeção Próximos 3 Meses")
        ult_3m = evo[evo['mes'] >= evo['mes'].max() - pd.DateOffset(months=3)]
        media_entrada = ult_3m[ult_3m['tipo']=='Entrada']['valor'].mean() if not ult_3m[ult_3m['tipo']=='Entrada'].empty else entradas/len(evo['mes'].unique()) if len(evo['mes'].unique())>0 else 0
        media_saida = ult_3m[ult_3m['tipo']=='Saida']['valor'].mean() if not ult_3m[ult_3m['tipo']=='Saida'].empty else saidas/len(evo['mes'].unique()) if len(evo['mes'].unique())>0 else 0

        proj_meses = [evo['mes'].max() + pd.DateOffset(months=i) for i in range(1,4)]
        proj_df = pd.DataFrame({
            "mes": proj_meses*2,
            "tipo": ["Entrada"]*3 + ["Saida"]*3,
            "valor": [media_entrada]*3 + [media_saida]*3
        })
        fig_proj = go.Figure()
        fig_proj.add_trace(go.Bar(x=evo['mes'], y=evo[evo['tipo']=='Entrada']['valor'], name="Entrada Real", marker_color="green"))
        fig_proj.add_trace(go.Bar(x=evo['mes'], y=evo[evo['tipo']=='Saida']['valor'], name="Saída Real", marker_color="red"))
        fig_proj.add_trace(go.Scatter(x=proj_df[proj_df['tipo']=='Entrada']['mes'], y=proj_df[proj_df['tipo']=='Entrada']['valor'], name="Entrada Projetada", mode="lines+markers", line=dict(dash="dash", color="green")))
        fig_proj.add_trace(go.Scatter(x=proj_df[proj_df['tipo']=='Saida']['mes'], y=proj_df[proj_df['tipo']=='Saida']['valor'], name="Saída Projetada", mode="lines+markers", line=dict(dash="dash", color="red")))
        fig_proj.update_layout(title="Real vs Projeção Futura (média 3 meses)")
        st.plotly_chart(fig_proj, use_container_width=True, key="projecao")

# ============ LANÇAR - SEM DOWNLOAD DENTRO DO FORM ============
elif menu == "Lançar":
    with st.form("form_lancar", clear_on_submit=True):
        c1,c2 = st.columns(2)
        data_in = c1.date_input("Data*", value=date.today())
        tipo_in = c2.selectbox("Tipo*", ["Saida","Entrada"])
        item_in = st.text_input("Item / Descrição* Ex: Mercado, Aluguel, Salário")
        c3,c4 = st.columns(2)
        valor_in = c3.number_input("Valor R$*", min_value=0.0, step=10.0, format="%.2f")
        classe_in = c4.selectbox("Classe*", ["Alimentação","Transporte","Moradia","Lazer","Saúde","Educação","Moto","Trabalho","Salário","Investimento","Outros"])
        salvar = st.form_submit_button("💾 Lançar")
        if salvar:
            if not item_in or valor_in<=0:
                st.error("Preencha Item e Valor")
            else:
                nid = add_item(data_in, item_in, valor_in, tipo_in, classe_in)
                st.success(f"ID #{nid} lançado! R$ {valor_in:.2f} - {item_in}")
                st.rerun()

# ============ HISTÓRICO COM EDITAR E DELETAR ============
elif menu == "Histórico / Editar / Deletar":
    df_h = query_df()
    if df_h.empty:
        st.info("Sem lançamentos")
    else:
        c1,c2,c3 = st.columns(3)
        f_tipo = c1.multiselect("Filtrar Tipo", ["Entrada","Saida"], key="f_tipo")
        f_classe = c2.multiselect("Filtrar Classe", sorted(df_h['classe'].unique().tolist()), key="f_classe")
        f_item = c3.text_input("Buscar Item", key="f_item")

        df_f = df_h.copy()
        if f_tipo: df_f = df_f[df_f['tipo'].isin(f_tipo)]
        if f_classe: df_f = df_f[df_f['classe'].isin(f_classe)]
        if f_item: df_f = df_f[df_f['item'].str.contains(f_item, case=False, na=False)]

        st.dataframe(df_f, use_container_width=True, height=400)

        st.divider()
        st.subheader("✏️ Editar / 🗑️ Deletar")
        id_sel = st.selectbox("Selecione ID", df_f['id'].tolist(), key="sel_id_hist")
        dsel = query_df()
        dsel = dsel[dsel['id']==int(id_sel)]
        if dsel.empty:
            st.warning("ID não encontrado")
        else:
            d = dsel.iloc[0]
            c1,c2,c3 = st.columns([1,1,1])
            if c1.button(f"✏️ Editar #{id_sel}", use_container_width=True, key=f"btn_edit_{id_sel}"):
                st.session_state.edit_id = int(id_sel)
            if c2.button(f"🗑️ DELETAR #{id_sel}", type="primary", use_container_width=True, key=f"btn_del_{id_sel}"):
                delete_item(int(id_sel))
                st.session_state.edit_id = None
                st.success("Deletado!")
                st.rerun()
            if c3.button("Cancelar", use_container_width=True, key=f"btn_cancel_{id_sel}"):
                st.session_state.edit_id = None

            if st.session_state.edit_id == int(id_sel):
                with st.form(f"form_edit_{id_sel}"):
                    c1,c2 = st.columns(2)
                    data_e = c1.date_input("Data", value=pd.to_datetime(d['data']).date() if pd.notna(pd.to_datetime(d['data'], errors='coerce')) else date.today())
                    tipo_e = c2.selectbox("Tipo", ["Saida","Entrada"], index=0 if d['tipo']=="Saida" else 1)
                    item_e = st.text_input("Item", value=str(d['item']))
                    c3,c4 = st.columns(2)
                    valor_e = c3.number_input("Valor", value=float(d['valor'] or 0), step=10.0)
                    classe_e = c4.text_input("Classe", value=str(d['classe']))
                    if st.form_submit_button("💾 Salvar Edição"):
                        update_item(int(id_sel), data_e, item_e, valor_e, tipo_e, classe_e)
                        st.session_state.edit_id = None
                        st.success("Atualizado!")
                        st.rerun()

# ============ RESUMO EXCEL ============
elif menu == "Resumo Excel":
    df_r = query_df()
    if df_r.empty:
        st.info("Sem dados")
    else:
        df_r['valor'] = pd.to_numeric(df_r['valor'], errors='coerce').fillna(0)
        df_r['data'] = pd.to_datetime(df_r['data'], errors='coerce')
        df_r['mes'] = df_r['data'].dt.to_period('M').astype(str)

        entradas = df_r[df_r['tipo']=='Entrada']['valor'].sum()
        saidas = df_r[df_r['tipo']=='Saida']['valor'].sum()
        st.metric("Resumo", f"Entrada R$ {entradas:.2f} | Saída R$ {saidas:.2f} | Saldo R$ {entradas-saidas:.2f}")

        # 3 abas no excel
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as w:
            df_r.to_excel(w, sheet_name="Lancamentos", index=False)
            df_r.groupby(['mes','tipo'])['valor'].sum().reset_index().to_excel(w, sheet_name="Evolucao_Mensal", index=False)
            df_r.groupby('classe')['valor'].sum().reset_index().sort_values('valor', ascending=False).to_excel(w, sheet_name="Por_Classe", index=False)
            pd.DataFrame([{
                "Entradas": entradas, "Saidas": saidas, "Saldo": entradas-saidas,
                "Media Gasto": df_r[df_r['tipo']=='Saida']['valor'].mean(),
                "Economia %": (entradas-saidas)/entradas*100 if entradas>0 else 0
            }]).to_excel(w, sheet_name="Resumo", index=False)

        st.download_button("📥 Baixar Excel Resumo Financeiro Completo", buf.getvalue(), f"resumo_financeiro_{date.today()}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary", key="dl_resumo_excel")
