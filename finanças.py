import streamlit as st, pandas as pd, sqlite3
from datetime import date
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
if menu=="Dashboard" and not df.empty:
    df['valor']=pd.to_numeric(df['valor'],errors='coerce')
    e=df[df.tipo=="Entrada"].valor.sum()
    s=df[df.tipo=="Saida"].valor.sum()
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Entrada",f"R$ {e:.2f}"); c2.metric("Saida",f"R$ {s:.2f}"); c3.metric("Saldo",f"R$ {e-s:.2f}"); c4.metric("Média",f"R$ {df[df.tipo=='Saida'].valor.mean():.2f}")
    df['data']=pd.to_datetime(df['data']); df['mes']=df['data'].dt.strftime('%Y-%m')
    st.bar_chart(df.groupby(['mes','tipo']).valor.sum().reset_index(), x='mes', y='valor', color='tipo')
elif menu=="Lançar":
    d=st.date_input("Data",value=date.today()); t=st.selectbox("Tipo",["Saida","Entrada"]); i=st.text_input("Item"); cl=st.selectbox("Classe",["Alim","Transp","Moradia","Lazer","Salario","Outros"]); v=st.number_input("Valor",0.0,step=10.0)
    if st.button("Salvar"):
        cur.execute("INSERT INTO f (data,item,valor,tipo,classe) VALUES (?,?,?,?,?)",(str(d),i,v,t,cl)); conn.commit(); st.success("Salvo!"); st.rerun()
elif menu=="Editar" and not df.empty:
    st.dataframe(df, use_container_width=True)
    id_=st.number_input("ID",min_value=int(df.id.min()),max_value=int(df.id.max()),step=1)
    row=df[df.id==id_]
    if not row.empty:
        r=row.iloc[0]
        ni=st.text_input("Item",r['item']); nv=st.number_input("Valor",value=float(r['valor'])); nt=st.selectbox("Tipo",["Saida","Entrada"],index=0 if r['tipo']=="Saida" else 1)
        if st.button("Salvar Edição"): cur.execute("UPDATE f SET item=?,valor=?,tipo=? WHERE id=?",(ni,nv,nt,int(id_))); conn.commit(); st.rerun()
        if st.button("Deletar"): cur.execute("DELETE FROM f WHERE id=?",(int(id_),)); conn.commit(); st.rerun()
elif menu=="Excel" and not df.empty:
    buf=io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as w: df.to_excel(w,index=False)
    st.download_button("Baixar Excel",buf.getvalue(),"resumo.xlsx")
