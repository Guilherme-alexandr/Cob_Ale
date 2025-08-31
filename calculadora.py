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
    teto_juros = 1.0
    entrada_minima_fixa = 100.0

    juros_total = valor_original * juros_diario * dias_em_atraso
    juros_total = min(juros_total, valor_original * teto_juros)
    valor_com_juros = valor_original + juros_total

    desconto_max_avista = 0
    desconto_max_parcelado = 0

    if 60 <= dias_em_atraso <= 99:
        desconto_max_avista = 10
        desconto_max_parcelado = 3
    elif 100 <= dias_em_atraso <= 150:
        desconto_max_avista = 20
        desconto_max_parcelado = 8
    elif dias_em_atraso > 150:
        desconto_max_avista = 30
        desconto_max_parcelado = 15

    if desconto_max_avista or desconto_max_parcelado:
        faixa_inicio = 60 if dias_em_atraso <= 99 else (100 if dias_em_atraso <= 150 else 151)
        faixa_fim = 99 if dias_em_atraso <= 99 else (150 if dias_em_atraso <= 150 else dias_em_atraso)
        proporcao = (dias_em_atraso - faixa_inicio) / (faixa_fim - faixa_inicio + 1)

        desconto = desconto_max_avista * proporcao if tipo_pagamento == "avista" else desconto_max_parcelado * proporcao
    else:
        desconto = 0

    valor_desconto = valor_com_juros * (desconto / 100)
    valor_final = valor_com_juros - valor_desconto

    resultado = {
        "valor_original": round(valor_original, 2),
        "dias_em_atraso": dias_em_atraso,
        "tipo_pagamento": tipo_pagamento,
        "juros_total": round(juros_total, 2),
        "percentual_desconto": round(desconto, 2),
        "valor_desconto": round(valor_desconto, 2),
        "valor_final": round(valor_final, 2)
    }

    if tipo_pagamento == "parcelado":
        if not valor_entrada or valor_entrada <= 0:
            valor_entrada = max(entrada_minima_fixa, 0.0)
            if valor_entrada >= valor_final:
                valor_entrada = valor_final * 0.1
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
