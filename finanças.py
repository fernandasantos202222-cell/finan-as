elif menu=="Meta Sapato":
    st.subheader("🎯 Quero comprar sapato - Tenho saldo? + Projeção Investimento")
    nome_meta=st.text_input("O que?", value="Sapato", key="m_nome")
    valor_meta=st.number_input("Valor sapato", value=150.0, key="m_valor")
    if st.button("Salvar Meta", key="m_save"):
        cur.execute("INSERT INTO metas (nome,valor) VALUES (?,?)",(nome_meta,valor_meta)); conn.commit()

    df_fat=get_df("fatura")
    total_cartao = pd.to_numeric(df_fat.valor, errors='coerce').sum() if not df_fat.empty else 0
    df_all=get_df("f")
    saldo_disp = df_all[df_all.tipo=="Entrada"].valor.sum() - df_all[df_all.tipo=="Saida"].valor.sum() - total_cartao if not df_all.empty else -total_cartao

    st.metric("SALDO REAL hoje (descontando cartão)", f"R$ {saldo_disp:.2f}")

    # PROJEÇÃO DE INVESTIMENTO VOLTOU - COM EXPLICAÇÃO
    st.divider()
    st.subheader("📈 Projeção se investir")
    economia = st.slider("Quanto consegue guardar por mês?", 20, 500, 50, step=10, key="eco_inv")

    # Calculo
    saldo_inv = 0
    hist = []
    for mes in range(1,13):
        saldo_inv = (saldo_inv + economia) * 1.01  # 1% = CDB 12% ao ano
        hist.append({"Mês": mes, "Guardado na gaveta": economia*mes, "Investindo 1% a.m": round(saldo_inv,2)})

    df_proj = pd.DataFrame(hist)
    st.line_chart(df_proj, x="Mês", y=["Guardado na gaveta","Investindo 1% a.m"])

    # Resposta clara
    precisa = valor_meta / 3  # se quer em 3 meses
    if economia < precisa:
        st.error(f"❌ Quer em 3 meses? Precisa R$ {precisa:.2f}/mês. Guardando R$ {economia} você leva {valor_meta/economia:.1f} meses")
    else:
        st.success(f"✅ Com R$ {economia}/mês você compra em {valor_meta/economia:.1f} meses")

    if saldo_disp >= valor_meta:
        st.success(f"✅ PODE COMPRAR AGORA! Sobra R$ {saldo_disp-valor_meta:.2f}")
        st.info(f"""**Dica IA:**
        - Se pagar à vista: sobra R$ {saldo_disp-valor_meta:.2f}
        - Se parcelar 3x de R$ {valor_meta/3:.2f} e deixar R$ {valor_meta:.2f} no Nubank (1%): ganha R$ {valor_meta*0.01*3:.2f} de juros
        - Em 12 meses guardando R$ {economia}: sem investir R$ {economia*12:.2f} | investindo R$ {saldo_inv:.2f} (ganho R$ {saldo_inv-economia*12:.2f})
        """)
    else:
        falta = valor_meta - saldo_disp
        st.error(f"❌ Falta R$ {falta:.2f}")
        st.warning(f"Plano: Junte R$ {falta/3:.2f}/mês por 3 meses. Investindo, em 3 meses terá R$ {sum([economia*1.01**i for i in range(3)]):.2f}")

    # Editar/deletar
    df_metas=get_df("metas")
    if not df_metas.empty:
        st.dataframe(df_metas, use_container_width=True)
        id_m=st.number_input("ID meta deletar", min_value=int(df_metas.id.min()), max_value=int(df_metas.id.max()), key="id_meta")
        if st.button("Deletar Meta", key="del_meta"):
            cur.execute("DELETE FROM metas WHERE id=?",(int(id_m),)); conn.commit(); st.rerun()
