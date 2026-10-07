import streamlit as st, pandas as pd, sqlite3
from datetime import date, timedelta
import io

conn = sqlite3.connect("fin.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS f (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, item TEXT, valor REAL, tipo TEXT, classe TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS fatura (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, item TEXT, valor REAL, parcelas INT, cartao TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS metas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, valor REAL)")
cur = conn.cursor()

def get_df(tab):
    return pd.read_sql(f"SELECT * FROM {tab} ORDER BY id DESC", conn)

st.set_page_config(layout="wide")
st.title("💰 Finanças + Cartão + Meta")

periodo = st.sidebar.date_input("Período", value=(date.today()-timedelta(days=60), date.today()))
if isinstance(periodo, tuple) and len(periodo)==2:
    ini,fim = periodo
else:
    ini = fim = periodo[0] if isinstance(periodo, tuple) else periodo

menu = st.sidebar.radio("Menu", ["Dashboard","Lançar","Cartão","Meta Sapato","Excel"])

df = get_df("f")
if not df.empty:
    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df = df.dropna(subset=['data'])
    df = df[(df['data'].dt.date >= ini) & (df['data'].dt.date <= fim)]

if menu=="Dashboard":
    entradas = df[df.tipo=="Entrada"].valor.sum() if not df.empty else 0
    saidas = df[df.tipo=="Saida"].valor.sum() if not df.empty else 0
    df_fat = get_df("fatura")
    total_cartao = pd.to_numeric(df_fat.valor, errors='coerce').sum() if not df_fat.empty else 0
    saldo_real = entradas - saidas - total_cartao
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Entrada",f"R$ {entradas:.2f}"); c2.metric("Saída",f"R$ {saidas:.2f}"); c3.metric("Cartão",f"R$ {total_cartao:.2f}"); c4.metric("SALDO REAL",f"R$ {saldo_real:.2f}")
    if not df.empty:
        df['mes']=df['data'].dt.to_period('M').astype(str)
        evo=df.groupby(['mes','tipo']).valor.sum().reset_index()
        st.subheader(f"Evolução Mensal {ini} a {fim}")
        st.bar_chart(evo, x='mes', y='valor', color='tipo')
    st.divider()
    df_all=get_df("f")
    if not df_all.empty:
        st.dataframe(df_all, use_container_width=True)
        id_del=st.number_input("ID para deletar/editar", min_value=int(df_all.id.min()), max_value=int(df_all.id.max()), key="del_f")
        if st.button("🗑️ Deletar", key="del_f_btn"):
            cur.execute("DELETE FROM f WHERE id=?",(int(id_del),)); conn.commit(); st.rerun()

elif menu=="Lançar":
    d=st.date_input("Data",value=date.today(), key="d_l")
    t=st.selectbox("Tipo",["Saida","Entrada"], key="t_l")
    i=st.text_input("Item", key="i_l")
    cl=st.selectbox("Classe",["Alimentação","Transporte","Moradia","Lazer","Salário","Outros"], key="cl_l")
    v=st.number_input("Valor",0.0,step=10.0, key="v_l")
    if st.button("Salvar",type="primary", key="b_l") and i:
        cur.execute("INSERT INTO f (data,item,valor,tipo,classe) VALUES (?,?,?,?,?)",(str(d),i,v,t,cl)); conn.commit(); st.success("Salvo!")

elif menu=="Cartão":
    st.subheader("💳 Cartão")
    dc=st.date_input("Data compra", value=date.today(), key="dc")
    ic=st.text_input("O que comprou?", key="ic")
    vc=st.number_input("Valor total", 0.0, step=10.0, key="vc")
    parc=st.number_input("Parcelas", 1, 12, 1, key="parc")
    cart=st.text_input("Cartão", value="Nubank", key="cart_nome")
    if st.button("Lançar no Cartão", key="btn_cart"):
        cur.execute("INSERT INTO fatura (data,item,valor,parcelas,cartao) VALUES (?,?,?,?,?)",(str(dc),ic,vc,parc,cart)); conn.commit(); st.success("Lançado!")
    df_fat=get_df("fatura")
    if not df_fat.empty:
        st.dataframe(df_fat, use_container_width=True)
        id_f=st.number_input("ID fatura deletar", min_value=int(df_fat.id.min()), max_value=int(df_fat.id.max()), key="id_fat")
        if st.button("Deletar Fatura", key="del_fat"):
            cur.execute("DELETE FROM fatura WHERE id=?",(int(id_f),)); conn.commit(); st.rerun()

elif menu=="Meta Sapato":
    st.subheader("🎯 Meta + Projeção Investimento")
    nome_meta=st.text_input("O que?", value="Sapato", key="m_nome")
    valor_meta=st.number_input("Valor", value=150.0, key="m_valor")
    if st.button("Salvar Meta", key="m_save"):
        cur.execute("INSERT INTO metas (nome,valor) VALUES (?,?)",(nome_meta,valor_meta)); conn.commit()

    df_fat=get_df("fatura")
    total_cartao = pd.to_numeric(df_fat.valor, errors='coerce').sum() if not df_fat.empty else 0
    df_all=get_df("f")
    saldo_disp = df_all[df_all.tipo=="Entrada"].valor.sum() - df_all[df_all.tipo=="Saida"].valor.sum() - total_cartao if not df_all.empty else -total_cartao
    st.metric("SALDO REAL hoje", f"R$ {saldo_disp:.2f}")

    economia = st.slider("Quanto guardar por mês?", 20, 500, 50, step=10, key="eco_inv")
    precisa = valor_meta / 3
    if economia < precisa:
        st.error(f"❌ Para {valor_meta:.2f} em 3 meses precisa R$ {precisa:.2f}/mês. Com R$ {economia} leva {valor_meta/economia:.1f} meses")
    else:
        st.success(f"✅ Com R$ {economia}/mês consegue em {valor_meta/economia:.1f} meses")

    saldo_inv=0
    hist=[]
    for mes in range(1,13):
        saldo_inv=(saldo_inv+economia)*1.01
        hist.append({"Mês":mes,"Gaveta":economia*mes,"Investindo 1%":round(saldo_inv,2)})
    df_proj=pd.DataFrame(hist)
    st.line_chart(df_proj, x="Mês", y=["Gaveta","Investindo 1%"])

    if saldo_disp >= valor_meta:
        st.success(f"✅ PODE COMPRAR! Sobra R$ {saldo_disp-valor_meta:.2f}")
    else:
        st.error(f"❌ Falta R$ {valor_meta-saldo_disp:.2f}")

    df_metas=get_df("metas")
    if not df_metas.empty:
        st.dataframe(df_metas, use_container_width=True)
        id_m=st.number_input("ID meta deletar", min_value=int(df_metas.id.min()), max_value=int(df_metas.id.max()), key="id_meta")
        if st.button("Deletar Meta", key="del_meta"):
            cur.execute("DELETE FROM metas WHERE id=?",(int(id_m),)); conn.commit(); st.rerun()

elif menu=="Excel":
    df_all=get_df("f")
    df_fat=get_df("fatura")
    buf=io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as w:
        df_all.to_excel(w, sheet_name="Entradas_Saidas", index=False)
        df_fat.to_excel(w, sheet_name="Cartao", index=False)
    st.download_button("Baixar Excel", buf.getvalue(), "financeiro.xlsx", key="dl_all")
