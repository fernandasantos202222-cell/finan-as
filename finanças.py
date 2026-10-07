import streamlit as st, pandas as pd, sqlite3
from datetime import date, timedelta
import io

conn = sqlite3.connect("fin.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS f (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, item TEXT, valor REAL, tipo TEXT, classe TEXT)")
cur = conn.cursor()

def get_df():
    cur.execute("SELECT * FROM f ORDER BY id DESC")
    return pd.DataFrame(cur.fetchall(), columns=["id","data","item","valor","tipo","classe"])

st.set_page_config(layout="wide")
st.title("💰 Finanças")
menu = st.sidebar.radio("Menu",["Dashboard","Lançar","Editar","Excel"])

df = get_df()

# FILTRO POR PERIODO - ADICIONADO AGORA
st.sidebar.divider()
st.sidebar.write("📅 Filtro por Período")
periodo = st.sidebar.date_input("Período", value=(date.today()-timedelta(days=30), date.today()))

if not df.empty:
    df['data'] = pd.to_datetime(df['data'])
    if len(periodo)==2:
        df = df[(df['data'].dt.date >= periodo[0]) & (df['data'].dt.date <= periodo[1])]

if menu=="Dashboard":
    if df.empty:
        st.info("Sem dados no período")
    else:
        df['valor']=pd.to_numeric(df['valor'],errors='coerce')
        e=df[df.tipo=="Entrada"].valor.sum()
        s=df[df.tipo=="Saida"].valor.sum()
        c1,c2,c3,c4=st.columns(4)
        c1.metric("Entrada",f"R$ {e:.2f}")
        c2.metric("Saída",f"R$ {s:.2f}")
        c3.metric("Saldo",f"R$ {e-s:.2f}")
        c4.metric("Média Gasto",f"R$ {df[df.tipo=='Saida'].valor.mean():.2f}")

        df['mes']=df['data'].dt.strftime('%Y-%m')
        st.subheader(f"Evolução {periodo[0]} até {periodo[1]}")
        st.bar_chart(df.groupby(['mes','tipo']).valor.sum().reset_index(), x='mes', y='valor', color='tipo')
        st.dataframe(df, use_container_width=True)

elif menu=="Lançar":
    d=st.date_input("Data",value=date.today())
    t=st.selectbox("Tipo",["Saida","Entrada"])
    i=st.text_input("Item")
    cl=st.selectbox("Classe",["Alimentação","Transporte","Moradia","Lazer","Salário","Outros"])
    v=st.number_input("Valor",0.0,step=10.0)
    if st.button("Salvar",type="primary"):
        cur.execute("INSERT INTO f (data,item,valor,tipo,classe) VALUES (?,?,?,?,?)",(str(d),i,v,t,cl))
        conn.commit()
        st.success("Salvo!")

elif menu=="Editar" and not df.empty:
    st.dataframe(df, use_container_width=True)
    id_=st.number_input("ID para editar/deletar",min_value=int(df.id.min()),max_value=int(df.id.max()),step=1)
    if st.button("Deletar"):
        cur.execute("DELETE FROM f WHERE id=?",(int(id_),))
        conn.commit()
        st.rerun()

elif menu=="Excel":
    if df.empty:
        st.info("Sem dados no período")
    else:
        buf=io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as w:
            df.to_excel(w, sheet_name="Filtrado_Periodo", index=False)
        st.download_button(f"📥 Excel {periodo[0]} a {periodo[1]}",buf.getvalue(),f"financeiro_{periodo[0]}_{periodo[1]}.xlsx")
