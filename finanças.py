import streamlit as st, pandas as pd, sqlite3
from datetime import date, timedelta
import io

conn = sqlite3.connect("fin.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS f (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, item TEXT, valor REAL, tipo TEXT, classe TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS metas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, valor REAL, prazo INTEGER)")
cur = conn.cursor()

def get_df():
    cur.execute("SELECT * FROM f ORDER BY data DESC")
    return pd.DataFrame(cur.fetchall(), columns=["id","data","item","valor","tipo","classe"])

st.set_page_config(layout="wide")
st.title("💰 Finanças Inteligentes")
menu = st.sidebar.radio("Menu",["Dashboard","Lançar","Metas e Projeção","Excel"])

# FILTRO PERIODO COM CORREÇÃO DO ERRO DA SUA FOTO
st.sidebar.divider()
periodo = st.sidebar.date_input("Filtrar período", value=(date.today()-timedelta(days=60), date.today()))
# Corrige IndexError quando só tem 1 data selecionada
if isinstance(periodo, tuple) and len(periodo)==1:
    ini = fim = periodo[0]
elif isinstance(periodo, tuple) and len(periodo)==2:
    ini, fim = periodo
else:
    ini = fim = periodo

df = get_df()
if not df.empty:
    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df = df.dropna(subset=['data'])
    df = df[(df['data'].dt.date >= ini) & (df['data'].dt.date <= fim)]

if menu=="Dashboard":
    if df.empty:
        st.info(f"Sem dados de {ini} até {fim}")
    else:
        df['valor']=pd.to_numeric(df['valor'], errors='coerce').fillna(0)
        e=df[df.tipo=="Entrada"].valor.sum()
        s=df[df.tipo=="Saida"].valor.sum()
        c1,c2,c3,c4=st.columns(4)
        c1.metric("Entrada",f"R$ {e:.2f}"); c2.metric("Saída",f"R$ {s:.2f}"); c3.metric("Saldo",f"R$ {e-s:.2f}"); c4.metric("Média Gasto",f"R$ {df[df.tipo=='Saida'].valor.mean():.2f}")

        # EVOLUÇÃO MENSAL - CORRIGIDO
        st.subheader(f"Evolução Mensal - {ini} até {fim}")
        df['mes'] = df['data'].dt.to_period('M').astype(str)
        evo = df.groupby(['mes','tipo']).valor.sum().reset_index()
        if not evo.empty:
            st.bar_chart(evo, x='mes', y='valor', color='tipo', use_container_width=True)
        else:
            st.write("Sem dados para gráfico")

        st.dataframe(df, use_container_width=True)

elif menu=="Lançar":
    d=st.date_input("Data",value=date.today(), key="d1")
    t=st.selectbox("Tipo",["Saida","Entrada"], key="t1")
    i=st.text_input("Item", key="i1")
    cl=st.selectbox("Classe",["Alimentação","Transporte","Moradia","Lazer","Salário","Outros"], key="cl1")
    v=st.number_input("Valor",0.0,step=10.0, key="v1")
    if st.button("Salvar",type="primary", key="b1"):
        cur.execute("INSERT INTO f (data,item,valor,tipo,classe) VALUES (?,?,?,?,?)",(str(d),i,v,t,cl))
        conn.commit(); st.success("Salvo!")

elif menu=="Metas e Projeção":
    st.subheader("🎯 Criar Meta - Ex: Comprar Sapato")
    nome = st.text_input("O que quer comprar?", placeholder="Ex: Sapato R$ 300", key="meta_nome")
    c1,c2 = st.columns(2)
    valor_meta = c1.number_input("Valor da meta R$", min_value=0.0, step=50.0, key="meta_valor")
    prazo = c2.number_input("Em quantos meses?", min_value=1, max_value=60, value=3, key="meta_prazo")
    if st.button("Salvar Meta", key="meta_save"):
        cur.execute("INSERT INTO metas (nome,valor,prazo) VALUES (?,?,?)",(nome,valor_meta,prazo))
        conn.commit()
        st.success("Meta salva!")

    st.divider()
    cur.execute("SELECT * FROM metas ORDER BY id DESC")
    metas = pd.DataFrame(cur.fetchall(), columns=["id","nome","valor","prazo"])
    if not metas.empty:
        st.dataframe(metas, use_container_width=True)
        meta_sel = st.selectbox("Escolha meta para projetar", metas['nome'].tolist(), key="meta_sel")
        m = metas[metas['nome']==meta_sel].iloc[0]

        st.subheader(f"Projeção para: {m['nome']} - R$ {m['valor']:.2f} em {m['prazo']} meses")
        economia_mensal = st.slider("Quanto consegue economizar por mês?", 20, 2000, 200, step=20, key="eco_slider")

        # Calculo simples
        meses_necessarios = m['valor'] / economia_mensal if economia_mensal>0 else 0
        st.metric("Você consegue em", f"{meses_necessarios:.1f} meses")

        # Projeção com investimento 1% ao mês (CDB ~12% ano)
        saldo = 0
        historico = []
        for mes in range(1, int(m['prazo'])+1):
            saldo = (saldo + economia_mensal) * 1.01 # 1% juros
            historico.append({"Mês": mes, "Acumulado sem investir": economia_mensal*mes, "Com investimento 1%": saldo})

        df_proj = pd.DataFrame(historico)
        st.line_chart(df_proj, x="Mês", y=["Acumulado sem investir","Com investimento 1%"], use_container_width=True)

        st.info(f"""
        **Dica IA para sua meta {m['nome']}:**
        - Sem investir: R$ {economia_mensal * m['prazo']:.2f} em {m['prazo']} meses
        - Investindo em CDB 100% CDI (12% ano): R$ {saldo:.2f} - ganha R$ {saldo - economia_mensal*m['prazo']:.2f} de juros
        - Para comprar em {m['prazo']} meses precisa guardar R$ {m['valor']/m['prazo']:.2f}/mês
        - Você está guardando R$ {economia_mensal:.2f} -> {'✅ META BATIDA' if saldo>=m['valor'] else '❌ Precisa aumentar ou prazo maior'}

        **Onde investir esse valor:**
        1. Curto prazo (<6 meses): Caixinha Nubank, Tesouro Selic
        2. Médio prazo: CDB 100% CDI
        3. Sapato de R$ {m['valor']:.2f}: se parcelar sem juros, melhor deixar dinheiro rendendo
        """)

elif menu=="Excel":
    if df.empty:
        st.info("Sem dados")
    else:
        buf=io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as w:
            df.to_excel(w, index=False, sheet_name="Periodo")
            get_df().to_excel(w, index=False, sheet_name="Tudo")
        st.download_button(f"Baixar Excel {ini} a {fim}", buf.getvalue(), f"financeiro_{ini}_{fim}.xlsx", key="dl_excel")
