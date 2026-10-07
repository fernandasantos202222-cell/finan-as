import streamlit as st, pandas as pd, sqlite3
from datetime import date, timedelta
import io

conn = sqlite3.connect("fin.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS f (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, item TEXT, valor REAL, tipo TEXT, classe TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS fatura (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, item TEXT, valor REAL, parcelas INT, cartao TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS metas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, valor REAL, prazo INT)")
cur = conn.cursor()
def get_df(t): return pd.read_sql(f"SELECT * FROM {t} ORDER BY id DESC", conn)

st.set_page_config(layout="wide")
st.title("💰 Minhas Finanças")

with st.sidebar:
    periodo = st.date_input("📅 Período", value=(date.today()-timedelta(days=60), date.today()))
    if isinstance(periodo, tuple) and len(periodo)==2: ini,fim=periodo
    else: ini=fim=periodo[0] if isinstance(periodo, tuple) else periodo
    menu = st.radio("Menu", ["1. Dashboard","2. Lançar","3. Cartão","4. Metas","5. Investimentos","6. IA"])

df = get_df("f")
df_filtrado = pd.DataFrame()
if not df.empty:
    df['data']=pd.to_datetime(df['data'], errors='coerce')
    df=df.dropna(subset=['data'])
    df_filtrado=df[(df['data'].dt.date>=ini) & (df['data'].dt.date<=fim)]

# FUNÇÃO EDITAR/DELETAR REUTILIZÁVEL
def bloco_editar_deletar(tabela, nome_id):
    st.divider()
    st.subheader(f"✏️ Editar / Deletar - {tabela}")
    df_tab=get_df(tabela)
    if df_tab.empty:
        st.info("Sem dados"); return
    st.dataframe(df_tab, use_container_width=True)
    id_sel=st.number_input(f"ID para {tabela}", min_value=int(df_tab.id.min()), max_value=int(df_tab.id.max()), key=f"id_{tabela}")
    row=df_tab[df_tab.id==id_sel]
    if row.empty: return
    r=row.iloc[0]
    c1,c2,c3=st.columns(3)
    if tabela=="f":
        novo_item=c1.text_input("Item", value=r['item'], key=f"edit_item_{tabela}_{id_sel}")
        novo_valor=c2.number_input("Valor", value=float(r['valor']), key=f"edit_val_{tabela}_{id_sel}")
        novo_tipo=c3.selectbox("Tipo", ["Saida","Entrada"], index=0 if r['tipo']=="Saida" else 1, key=f"edit_tipo_{tabela}_{id_sel}")
        if c1.button("Salvar Edição", key=f"save_{tabela}_{id_sel}"):
            cur.execute("UPDATE f SET item=?, valor=?, tipo=? WHERE id=?",(novo_item,novo_valor,novo_tipo,int(id_sel))); conn.commit(); st.success("Editado!"); st.rerun()
    elif tabela=="fatura":
        novo_item=c1.text_input("Item", value=r['item'], key=f"edit_item_{tabela}_{id_sel}")
        novo_valor=c2.number_input("Valor", value=float(r['valor']), key=f"edit_val_{tabela}_{id_sel}")
        nova_parc=c3.number_input("Parcelas", value=int(r['parcelas']), min_value=1, max_value=12, key=f"edit_parc_{tabela}_{id_sel}")
        if c1.button("Salvar Edição", key=f"save_{tabela}_{id_sel}"):
            cur.execute("UPDATE fatura SET item=?, valor=?, parcelas=? WHERE id=?",(novo_item,novo_valor,int(nova_parc),int(id_sel))); conn.commit(); st.success("Editado!"); st.rerun()
    elif tabela=="metas":
        novo_nome=c1.text_input("Nome", value=r['nome'], key=f"edit_nome_{tabela}_{id_sel}")
        novo_valor=c2.number_input("Valor", value=float(r['valor']), key=f"edit_val_{tabela}_{id_sel}")
        novo_prazo=c3.number_input("Prazo", value=int(r['prazo']), min_value=1, max_value=60, key=f"edit_prazo_{tabela}_{id_sel}")
        if c1.button("Salvar Edição", key=f"save_{tabela}_{id_sel}"):
            cur.execute("UPDATE metas SET nome=?, valor=?, prazo=? WHERE id=?",(novo_nome,novo_valor,int(novo_prazo),int(id_sel))); conn.commit(); st.success("Editado!"); st.rerun()
    if st.button(f"🗑️ Deletar ID {id_sel} de {tabela}", key=f"del_{tabela}_{id_sel}"):
        cur.execute(f"DELETE FROM {tabela} WHERE id=?",(int(id_sel),)); conn.commit(); st.success("Deletado!"); st.rerun()

if menu=="1. Dashboard":
    entradas=df_filtrado[df_filtrado.tipo=="Entrada"].valor.sum() if not df_filtrado.empty else 0
    saidas=df_filtrado[df_filtrado.tipo=="Saida"].valor.sum() if not df_filtrado.empty else 0
    total_cartao=pd.to_numeric(get_df("fatura").valor, errors='coerce').sum()
    saldo=entradas-saidas-total_cartao
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Entrada",f"R$ {entradas:.2f}"); c2.metric("Saída",f"R$ {saidas:.2f}"); c3.metric("Cartão",f"R$ {total_cartao:.2f}"); c4.metric("SALDO REAL",f"R$ {saldo:.2f}")
    if not df_filtrado.empty:
        df_filtrado['mes']=df_filtrado['data'].dt.to_period('M').astype(str)
        st.bar_chart(df_filtrado.groupby(['mes','tipo']).valor.sum().reset_index(), x='mes', y='valor', color='tipo')
    st.dataframe(df_filtrado, use_container_width=True)
    # AQUI TAMBÉM TEM EDITAR/DELETAR
    bloco_editar_deletar("f", "entradas")

elif menu=="2. Lançar":
    st.header("Lançar")
    with st.form("form_l"):
        d=st.date_input("Data",value=date.today()); t=st.selectbox("Tipo",["Saida","Entrada"]); i=st.text_input("Item"); cl=st.selectbox("Classe",["Alimentação","Transporte","Moradia","Lazer","Salário","Outros"]); v=st.number_input("Valor",0.0,step=10.0)
        if st.form_submit_button("Salvar"):
            cur.execute("INSERT INTO f (data,item,valor,tipo,classe) VALUES (?,?,?,?,?)",(str(d),i,v,t,cl)); conn.commit(); st.success("Salvo!")
    bloco_editar_deletar("f", "lancar")

elif menu=="3. Cartão":
    st.header("💳 Cartão")
    with st.form("form_c"):
        dc=st.date_input("Data",value=date.today()); ic=st.text_input("O que comprou?"); vc=st.number_input("Valor",0.0,step=10.0); parc=st.number_input("Parcelas",1,12,1); cart=st.text_input("Cartão",value="Nubank")
        if st.form_submit_button("Lançar"):
            cur.execute("INSERT INTO fatura (data,item,valor,parcelas,cartao) VALUES (?,?,?,?,?)",(str(dc),ic,vc,parc,cart)); conn.commit(); st.success("Lançado!")
    bloco_editar_deletar("fatura", "cartao")

elif menu=="4. Metas":
    st.header("🎯 Metas")
    with st.form("form_m"):
        nome=st.text_input("O que comprar?",placeholder="Sapato"); valor=st.number_input("Valor",0.0,step=10.0); prazo=st.number_input("Prazo meses",1,24,3)
        if st.form_submit_button("Salvar Meta"):
            cur.execute("INSERT INTO metas (nome,valor,prazo) VALUES (?,?,?)",(nome,valor,prazo)); conn.commit(); st.success("Meta salva!")
    bloco_editar_deletar("metas", "metas")

elif menu=="5. Investimentos":
    st.header("📈 Investimentos")
    economia=st.slider("Guardar por mês",20,1000,100,step=20)
    taxa=st.selectbox("Onde?",["Nubank 1%","Selic 0.8%","CDB 1.2%"])
    tv=0.01 if "1%" in taxa and "1.2%" not in taxa else 0.008 if "0.8%" in taxa else 0.012
    saldo_inv=0; hist=[]
    for mes in range(1,25):
        saldo_inv=(saldo_inv+economia)*(1+tv)
        hist.append({"Mês":mes,"Gaveta":economia*mes,"Investindo":round(saldo_inv,2)})
    df_p=pd.DataFrame(hist)
    st.line_chart(df_p, x="Mês", y=["Gaveta","Investindo"])
    st.dataframe(df_p.tail(12), use_container_width=True)

elif menu=="6. IA":
    st.header("🤖 IA Financeira")
    df_all=get_df("f"); df_fat=get_df("fatura")
    saldo = df_all[df_all.tipo=="Entrada"].valor.sum() - df_all[df_all.tipo=="Saida"].valor.sum() - pd.to_numeric(df_fat.valor,errors='coerce').sum() if not df_all.empty else 0
    st.metric("Saldo Real",f"R$ {saldo:.2f}")
    if not df_all.empty and not df_all[df_all.tipo=="Saida"].empty:
        por_classe=df_all[df_all.tipo=="Saida"].groupby('classe').valor.sum().sort_values(ascending=False)
        st.warning(f"IA: Seu maior gasto é {por_classe.index[0]} R$ {por_classe.iloc[0]:.2f}. Corte 20% = economiza R$ {por_classe.iloc[0]*0.2:.2f}")
    df_metas=get_df("metas")
    if not df_metas.empty:
        for _,m in df_metas.iterrows():
            falta=m.valor-saldo
            if falta<=0: st.success(f"✅ IA: Pode comprar {m.nome}! Sobra R$ {saldo-m.valor:.2f}")
            else: st.error(f"❌ IA: Falta R$ {falta:.2f} para {m.nome}. Guarde R$ {falta/3:.2f}/mês no Nubank")
