"""Conta do simulador de Home Equity (referência em Python; src/simulador.js usa a mesma conta, gerada em calculo.js, e os testes comparam as duas).

Modelo: parcela fixa (tabela Price, padrão) ou parcelas que caem (SAC) sobre o crédito total, com taxa de referência = taxa do parceiro + IPCA.
O SAC é uma opção de simulação na mesma taxa: o parceiro confirma na proposta quais sistemas oferece.
  - taxa do parceiro: "a partir de 1,09% a.m. + IPCA" (página pública do parceiro, conferida em 18/11/2026);
  - IPCA: o acumulado em 12 meses do IBGE (série SGS 13522 do Banco Central), convertido em taxa mensal e mantido constante na simulação;
  - limite: o parceiro divulga que libera "até 60% do valor do imóvel" e prazo "até 20 anos".
É ESTIMATIVA: a taxa e o limite finais saem da análise do parceiro. Não inclui IOF, avaliação do imóvel, registro em cartório nem seguros.
"""

TAXA_PARCEIRO_AM = 1.09   # % ao mês, "a partir de"
LTV_MAX = 0.60            # fração do valor do imóvel
CREDITO_MAX = 3_000_000   # teto de crédito da interface: teto comum de mercado (R$ 3 mi em Creditas e Neon); não é regra do parceiro
PRAZO_MAX_MESES = 240     # 20 anos
PRAZO_MIN_ANOS = 2       # limite de interface (o parceiro só divulga o máximo)
PRAZO_MAX_ANOS = 20
IMOVEL_MIN = 100_000
IMOVEL_MAX = 20_000_000
RECEBER_MIN = 50_000
SISTEMAS = ("price", "sac")  # price = parcela fixa; sac = amortização constante, parcela que cai
RENDA_REFERENCIA = 0.30      # referência de mercado (política de crédito das instituições), não regra do parceiro nem norma específica de Home Equity


def ipca_mensal(ipca_12m):
    """IPCA acumulado em 12 meses (% a.a.) -> taxa mensal equivalente, em fração (juros compostos)."""
    return (1 + ipca_12m / 100) ** (1 / 12) - 1


def taxa_mensal(ipca_12m, base_am=TAXA_PARCEIRO_AM):
    """Taxa de referência ao mês, em fração: (1 + base) x (1 + IPCA mensal) - 1."""
    return (1 + base_am / 100) * (1 + ipca_mensal(ipca_12m)) - 1


def pmt(principal, i, n):
    """Parcela fixa (Price). i em fração ao mês, n em meses."""
    if n <= 0:
        raise ValueError("prazo precisa ser positivo")
    if i == 0:
        return principal / n
    return principal * i / (1 - (1 + i) ** -n)


def valor_presente(parcela, i, n):
    """Crédito que gera esta parcela (inverso do pmt)."""
    if i == 0:
        return parcela * n
    return parcela * (1 - (1 + i) ** -n) / i


def valor_presente_sac(primeira_parcela, i, n):
    """Crédito cuja PRIMEIRA parcela no SAC é primeira_parcela (primeira = credito/n + credito*i)."""
    return primeira_parcela / (1 / n + i)


def plano(credito, i, meses, sistema="price"):
    """(primeira parcela, última parcela, total pago). No Price as duas parcelas são iguais; no SAC a parcela cai todo mês."""
    if sistema == "sac":
        amort = credito / meses
        return amort + credito * i, amort * (1 + i), credito + credito * i * (meses + 1) / 2
    p = pmt(credito, i, meses)
    return p, p, p * meses


def acumulado_mensal(credito, i, meses, sistema="price"):
    """Total pago até o fim de cada mês (índice 0 = 0). Dá a linha do gráfico 'quanto você terá pago ao longo do tempo'."""
    saida = [0.0]
    total = 0.0
    if sistema == "sac":
        amort = credito / meses
        saldo = credito
        for _ in range(meses):
            total += amort + saldo * i
            saldo -= amort
            saida.append(total)
        return saida
    p = pmt(credito, i, meses)
    return [p * k for k in range(meses + 1)]


def renda_para_parcela(parcela, fracao=RENDA_REFERENCIA):
    """Renda mensal em que a parcela ocupa a fração dada (referência de 30%)."""
    return parcela / fracao


def limite_credito(valor_imovel):
    return min(LTV_MAX * valor_imovel, CREDITO_MAX)


def receber_maximo(valor_imovel, saldo):
    return max(0.0, limite_credito(valor_imovel) - saldo)


def simular(valor_imovel, receber, saldo, meses, i, sistema="price"):
    """Devolve parcela (a primeira, no SAC), última parcela, total, juros e a relação crédito/imóvel. credito = o que você recebe + o saldo do financiamento que o novo crédito quita."""
    credito = receber + saldo
    parcela, ultima, total = plano(credito, i, meses, sistema)
    return {
        "credito": credito,
        "parcela": parcela,
        "parcela_final": ultima,
        "total": total,
        "juros": total - credito,
        "ltv": credito / valor_imovel if valor_imovel > 0 else 0.0,
        "limite": limite_credito(valor_imovel),
        "acima_limite": credito > limite_credito(valor_imovel) + 1e-9,
    }


def amortizacao_anual(credito, i, meses, sistema="price"):
    """Como a dívida cai ano a ano (Price: parcela fixa; SAC: amortização constante): juros pagos, amortização e saldo devedor no fim de cada ano."""
    parcela = pmt(credito, i, meses)
    amort_sac = credito / meses
    saldo = credito
    linhas = []
    restante = meses
    ano = 0
    while restante > 0:
        ano += 1
        juros = amortizado = 0.0
        for _ in range(min(12, restante)):
            j = saldo * i
            a = amort_sac if sistema == "sac" else parcela - j
            saldo -= a
            juros += j
            amortizado += a
        restante -= 12
        linhas.append({"ano": ano, "juros": juros, "amortizacao": amortizado, "saldo": saldo if saldo > 0.005 else 0.0})
    return linhas


def amortizar_antes(credito, i, meses, sistema="price", extra_mensal=0.0, unico=0.0, mes_unico=0, modo="prazo"):
    """Efeito de pagar a mais: `extra_mensal` em toda parcela e/ou `unico` no começo do mês `mes_unico` (0 = antes da 1ª parcela).
    modo "prazo": a parcela segue igual e a dívida acaba antes; "parcela": depois do valor único a parcela é recalculada para o prazo restante (o extra mensal sempre encurta o prazo).
    Devolve meses até quitar, total pago (parcelas + extras), juros e a primeira parcela depois do valor único (no SAC, a parcela daquele mês)."""
    saldo = credito
    parcela = pmt(credito, i, meses)
    amort = credito / meses
    total = 0.0
    nova = None
    for m in range(meses):
        if m == mes_unico and unico > 0:
            u = min(unico, saldo)
            saldo -= u
            total += u
            if modo == "parcela" and saldo > 0.005:
                parcela = pmt(saldo, i, meses - m)
                amort = saldo / (meses - m)
        if saldo <= 0.005:
            return {"meses": m, "total": total, "juros": total - credito, "parcela_nova": nova}
        j = saldo * i
        pago = (amort + j if sistema == "sac" else parcela) + extra_mensal
        pago = min(pago, saldo + j)
        if m == mes_unico and nova is None:
            nova = amort + j if sistema == "sac" else parcela
        saldo -= pago - j
        total += pago
    return {"meses": meses, "total": total, "juros": total - credito, "parcela_nova": nova}


def comparar_quitacao(divida, taxa_divida_am, meses, i, sistema="price"):
    """Mesma dívida e mesmo prazo: parcela e total na taxa da dívida (taxa_divida_am em fração ao mês, sempre parcela fixa) e no Home Equity (taxa i, no sistema escolhido).
    Com SAC, a parcela do Home Equity é a primeira. juros_mes1 = o que a dívida cobra de juros só no primeiro mês."""
    atual = pmt(divida, taxa_divida_am, meses)
    he, _, total_he = plano(divida, i, meses, sistema)
    return {
        "divida": divida,
        "parcela_atual": atual, "total_atual": atual * meses, "juros_mes1": divida * taxa_divida_am,
        "parcela_he": he, "total_he": total_he,
        "economia_mes": atual - he, "economia_total": atual * meses - total_he,
    }


def receber_para_parcela(parcela_alvo, valor_imovel, saldo, meses, i, passo=5000, sistema="price"):
    """Maior valor a receber (múltiplo de `passo`) cuja parcela (a primeira, no SAC) cabe em parcela_alvo; 0 se nem o menor valor cabe."""
    bruto = (valor_presente_sac(parcela_alvo, i, meses) if sistema == "sac" else valor_presente(parcela_alvo, i, meses)) - saldo
    return max(0, int(bruto // passo) * passo)
