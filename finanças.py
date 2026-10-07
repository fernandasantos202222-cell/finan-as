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
        min_value=0.01,
        step=0.01
    )

    tipo = st.radio(
        "Tipo",
        ["Entrada", "Saída"],
        horizontal=True
    )

    categoria = st.selectbox(
        "Categoria",
        [
            "Salário",
            "Moradia",
            "Alimentação",
            "Transporte",
            "Saúde",
            "Lazer",
            "Educação",
            "Investimentos",
            "Outros"
        ]
    )

    salvar = st.form_submit_button(
        "Salvar"
    )

if salvar:

    if descricao.strip() == "":
        st.error("Informe a descrição")
    else:

        df = carregar_dados()

        novo_id = (
            1
            if df.empty
            else int(df["ID"].max()) + 1
        )

        novo = pd.DataFrame([{
            "ID": novo_id,
            "Data": pd.Timestamp(data),
            "Descricao": descricao,
            "Valor": float(valor),
            "Tipo": tipo,
            "Categoria": categoria
        }])

        df = pd.concat(
            [df, novo],
            ignore_index=True
        )

        salvar_dados(df)

        st.success(
            "✅ Lançamento salvo"
        )
