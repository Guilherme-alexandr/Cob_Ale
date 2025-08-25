def calcular(payload):
    try:
        valor_original = float(payload.get('valor_original', 0))
        dias_em_atraso = int(payload.get('dias_em_atraso', 0))
        tipo_pagamento = payload.get('tipo_pagamento', '').lower()
        quantidade_parcelas = int(payload.get('quantidade_parcelas', 0) or 0)
        valor_entrada = payload.get('valor_entrada')
        valor_entrada = float(valor_entrada) if valor_entrada not in [None, '', 0] else None
    except (ValueError, TypeError):
        raise ValueError("Parâmetros inválidos enviados para o cálculo.")

    if tipo_pagamento not in ['avista', 'parcelado']:
        raise ValueError("Tipo de pagamento inválido. Use 'avista' ou 'parcelado'.")
    if tipo_pagamento == "parcelado" and (quantidade_parcelas < 2 or quantidade_parcelas > 24):
        raise ValueError("Parcelamento deve ser entre 2x e 24x.")

    juros_diario = 0.005
    juros_total = valor_original * juros_diario * dias_em_atraso
    valor_com_juros = valor_original + juros_total

    desconto = 0
    if 60 <= dias_em_atraso <= 99:
        if tipo_pagamento == "avista":
            desconto = 10
    elif 100 <= dias_em_atraso <= 150:
        if tipo_pagamento == "avista":
            desconto = 15
        elif tipo_pagamento == "parcelado":
            desconto = 5

    valor_desconto = valor_com_juros * (desconto / 100)
    valor_final = valor_com_juros - valor_desconto

    resultado = {
        "valor_original": round(valor_original, 2),
        "dias_em_atraso": dias_em_atraso,
        "tipo_pagamento": tipo_pagamento,
        "juros_total": round(juros_total, 2),
        "percentual_desconto": desconto,
        "valor_desconto": round(valor_desconto, 2),
        "valor_final": round(valor_final, 2)
    }

    if tipo_pagamento == "parcelado":
        if not valor_entrada or valor_entrada <= 0:
            valor_entrada = round(valor_final * 0.10, 2)
        elif valor_entrada >= valor_final:
            raise ValueError("Valor de entrada não pode ser maior ou igual ao valor final.")

        restante = valor_final - valor_entrada
        valor_parcela = round(restante / quantidade_parcelas, 2)

        resultado["parcelamento"] = {
            "entrada": round(valor_entrada, 2),
            "quantidade_parcelas": quantidade_parcelas,
            "valor_parcela": valor_parcela,
            "valor_total_parcelas": round(valor_parcela * quantidade_parcelas, 2)
        }

    return resultado
