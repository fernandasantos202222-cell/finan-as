import streamlit as st, pandas as pd, sqlite3
from datetime import date, timedelta
import io

conn = sqlite3.connect("fin.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS f (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, item TEXT, valor REAL, tipo TEXT, classe TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS fatura (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, item TEXT, valor REAL, parcelas INT, cartao TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS metas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, valor REAL, prazo INT)")
cur = conn.cursor()

def get_df(t):
    try: return pd.read_sql(f"SELECT * FROM {t} ORDER BY id DESC", conn)
    except: return pd.DataFrame()

st.set_page_config(layout="wide")
st.title("💰 Minhas Finanças")

with st.sidebar:
    periodo = st.date_input("📅 Período do resumo", value=(date.today()-timedelta(days=30), date.today()))
    if isinstance(periodo, tuple) and len(periodo)==2: ini,fim=periodo
    else: ini=fim=periodo[0] if isinstance(periodo, tuple) else periodo
    menu = st.radio("Menu", ["1. Dashboard","2. Lançar","3. Cartão","4. Metas","5. Investimentos","6. IA"])

    st.divider()
    st.subheader("💾 Backup / Excel")

    df_all=get_df("f"); df_fat=get_df("fatura"); df_met=get_df("metas")

    # 1. BACKUP COMPLETO
    buf1=io.BytesIO()
    with pd.ExcelWriter(buf1, engine='openpyxl') as w:
        df_all.to_excel(w, sheet_name="f", index=False)
        df_fat.to_excel(w, sheet_name="fatura", index=False)
        df_met.to_excel(w, sheet_name="metas", index=False)
    st.download_button("⬇️ Baixar BACKUP", buf1.getvalue(), f"backup_{date.today()}.xlsx", use_container_width=True)

    # 2. RESUMO POR PERIODO QUE VOCÊ ESCOLHEU
    if not df_all.empty:
        df_all['data_dt'] = pd.to_datetime(df_all['data'], errors='coerce')
        df_per = df_all[(df_all['data_dt'].dt.date>=ini) & (df_all['data_dt'].dt.date<=fim)].copy()

        entradas = df_per[df_per.tipo=="Entrada"].valor.sum()
        saidas = df_per[df_per.tipo=="Saida"].valor.sum()
        por_classe = df_per[df_per.tipo=="Saida"].groupby("classe").valor.sum().reset_index()
        saldo_periodo = entradas - saidas

        # monta resumo
        resumo_df = pd.DataFrame([
            {"Resumo do Período": f"{ini} até {fim}"},
            {"Item": "Total Entradas", "Valor": entradas},
            {"Item": "Total Saídas", "Valor": saidas},
            {"Item": "Saldo do Período", "Valor": saldo_periodo},
            {"Item": "Total Fatura Cartão (geral)", "Valor": pd.to_numeric(df_fat.valor, errors='coerce').sum()},
        ])

        buf2=io.BytesIO()
        with pd.ExcelWriter(buf2, engine='openpyxl') as w:
            resumo_df.to_excel(w, sheet_name=f"Resumo {ini} a {fim}", index=False)
            por_classe.to_excel(w, sheet_name="Gastos por Classe", index=False)
            df_per.drop(columns=['data_dt']).to_excel(w, sheet_name="Detalhe Periodo", index=False)
            df_fat.to_excel(w, sheet_name="Cartao", index=False)

        st.download_button(f"📊 Baixar Excel Resumo {ini} a {fim}", buf2.getvalue(), f"RESUMO_{ini}_a_{fim}.xlsx", type="primary", use_container_width=True)
    else:
        st.info("Sem lançamentos para resumo")

    st.divider()
    st.subheader("⬆️ Restaurar")
    up = st.file_uploader("Se sumiu, suba o backup aqui", type=["xlsx"], key="up")
    if up:
        try:
            xls = pd.ExcelFile(up)
            # LIMPA TUDO E INSERE DE NOVO COM ID
            for sheet_name in xls.sheet_names:
                tabela = sheet_name
                if sheet_name == "Lancamentos": tabela="f"
                if sheet_name == "Cartao": tabela="fatura"
                if sheet_name not in ["f","fatura","metas"]: continue
                df_up = pd.read_excel(xls, sheet_name=sheet_name)
                if df_up.empty: continue
                cur.execute(f"DELETE FROM {tabela}")
                conn.commit()
                # garante colunas
                df_up.to_sql(tabela, conn, if_exists="append", index=False)
            st.success("✅ Restaurado com sucesso! Recarregando...")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao restaurar: {e}")

# DADOS FILTRADOS
df = get_df("f")
df_filtrado = pd.DataFrame()
if not df.empty:
    df['data']=pd.to_datetime(df['data'], errors='coerce')
    df=df.dropna(subset=['data'])
    df_filtrado=df[(df['data'].dt.date>=ini) & (df['data'].dt.date<=fim)]

def bloco_editar_deletar(tabela):
    st.divider()
    st.subheader(f"✏️ Editar / Deletar - {tabela}")
    df_tab=get_df(tabela)
    if df_tab.empty: st.info("Sem dados"); return
    st.dataframe(df_tab, use_container_width=True)
    id_sel=st.number_input(f"ID {tabela}", min_value=int(df_tab.id.min()), max_value=int(df_tab.id.max()), key=f"id_{tabela}_{menu}")
    row=df_tab[df_tab.id==id_sel]
    if row.empty: return
    r=row.iloc[0]
    c1,c2,c3=st.columns(3)
    if tabela=="f":
        ni=c1.text_input("Item", value=r['item'], key=f"ei_{id_sel}_{menu}")
        nv=c2.number_input("Valor", value=float(r['valor']), key=f"ev_{id_sel}_{menu}")
        nt=c3.selectbox("Tipo", ["Saida","Entrada"], index=0 if r['tipo']=="Saida" else 1, key=f"et_{id_sel}_{menu}")
        if st.button("Salvar", key=f"s_{tabela}_{id_sel}_{menu}"):
            cur.execute("UPDATE f SET item=?, valor=?, tipo=? WHERE id=?",(ni,nv,nt,int(id_sel))); conn.commit(); st.rerun()
    elif tabela=="fatura":
        ni=c1.text_input("Item", value=r['item'], key=f"ei_f_{id_sel}_{menu}")
        nv=c2.number_input("Valor", value=float(r['valor']), key=f"ev_f_{id_sel}_{menu}")
        np=c3.number_input("Parcelas", value=int(r['parcelas']), min_value=1, max_value=12, key=f"ep_{id_sel}_{menu}")
        if st.button("Salvar", key=f"s_{tabela}_{id_sel}_{menu}"):
            cur.execute("UPDATE fatura SET item=?, valor=?, parcelas=? WHERE id=?",(ni,nv,int(np),int(id_sel))); conn.commit(); st.rerun()
    elif tabela=="metas":
        nn=c1.text_input("Nome", value=r['nome'], key=f"en_{id_sel}_{menu}")
        nv=c2.number_input("Valor", value=float(r['valor']), key=f"ev_m_{id_sel}_{menu}")
        np=c3.number_input("Prazo", value=int(r['prazo']), min_value=1, key=f"ep_m_{id_sel}_{menu}")
        if st.button("Salvar", key=f"s_{tabela}_{id_sel}_{menu}"):
            cur.execute("UPDATE metas SET nome=?, valor=?, prazo=? WHERE id=?",(nn,nv,int(np),int(id_sel))); conn.commit(); st.rerun()
    if st.button(f"🗑️ Deletar ID {id_sel}", key=f"d_{tabela}_{id_sel}_{menu}"):
        cur.execute(f"DELETE FROM {tabela} WHERE id=?",(int(id_sel),)); conn.commit(); st.rerun()

if menu=="1. Dashboard":
    entradas=df_filtrado[df_filtrado.tipo=="Entrada"].valor.sum() if not df_filtrado.empty else 0
    saidas=df_filtrado[df_filtrado.tipo=="Saida"].valor.sum() if not df_filtrado.empty else 0
    total_cartao=pd.to_numeric(get_df("fatura").valor, errors='coerce').sum()
    saldo=entradas-saidas-total_cartao
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Entradas período",f"R$ {entradas:.2f}"); c2.metric("Saídas período",f"R$ {saidas:.2f}"); c3.metric("Cartão",f"R$ {total_cartao:.2f}"); c4.metric("SALDO",f"R$ {saldo:.2f}")
    bloco_editar_deletar("f")
elif menu=="2. Lançar":
    with st.form("fl"):
        d=st.date_input("Data",value=date.today()); t=st.selectbox("Tipo",["Saida","Entrada"]); i=st.text_input("Item"); cl=st.selectbox("Classe",["Alimentação","Transporte","Moradia","Lazer","Salário","Outros"]); v=st.number_input("Valor",0.0,step=10.0)
        if st.form_submit_button("Salvar"): cur.execute("INSERT INTO f (data,item,valor,tipo,classe) VALUES (?,?,?,?,?)",(str(d),i,v,t,cl)); conn.commit(); st.success("Salvo!")
    bloco_editar_deletar("f")
elif menu=="3. Cartão":
    with st.form("fc"):
        dc=st.date_input("Data",value=date.today()); ic=st.text_input("O que comprou?"); vc=st.number_input("Valor",0.0,step=10.0); parc=st.number_input("Parcelas",1,12,1); cart=st.text_input("Cartão",value="Nubank")
        if st.form_submit_button("Lançar"): cur.execute("INSERT INTO fatura (data,item,valor,parcelas,cartao) VALUES (?,?,?,?,?)",(str(dc),ic,vc,parc,cart)); conn.commit()
    bloco_editar_deletar("fatura")
elif menu=="4. Metas":
    with st.form("fm"):
        nome=st.text_input("O que comprar?",value="Sapato"); valor=st.number_input("Valor",0.0,step=10.0); prazo=st.number_input("Prazo meses",1,24,3)
        if st.form_submit_button("Salvar Meta"): cur.execute("INSERT INTO metas (nome,valor,prazo) VALUES (?,?,?)",(nome,valor,prazo)); conn.commit()
    bloco_editar_deletar("metas")
elif menu=="5. Investimentos":
    economia=st.slider("Guardar por mês",20,1000,100,step=20)
    s=0; hist=[]
    for mes in range(1,25):
        s=(s+economia)*1.01; hist.append({"Mês":mes,"Gaveta":economia*mes,"Investindo":round(s,2)})
    st.line_chart(pd.DataFrame(hist), x="Mês", y=["Gaveta","Investindo"])
elif menu=="6. IA":
    df_all=get_df("f"); df_fat=get_df("fatura")
    saldo = df_all[df_all.tipo=="Entrada"].valor.sum() - df_all[df_all.tipo=="Saida"].valor.sum() - pd.to_numeric(df_fat.valor,errors='coerce').sum() if not df_all.empty else 0
    st.metric("Saldo Real",f"R$ {saldo:.2f}")
