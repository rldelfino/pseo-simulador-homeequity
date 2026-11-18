"""Conta do simulador de Home Equity (referência em Python; src/simulador.js usa a mesma conta, gerada em calculo.js, e os testes comparam as duas).

Modelo: parcela fixa (tabela Price) sobre o crédito total, com taxa de referência = taxa do parceiro + IPCA.
  - taxa do parceiro: "a partir de 1,09% a.m. + IPCA" (página pública do parceiro, conferida em 18/11/2026);
  - IPCA: o acumulado em 12 meses do IBGE (série SGS 13522 do Banco Central), convertido em taxa mensal e mantido constante na simulação;
  - limite: o parceiro divulga que libera "até 60% do valor do imóvel" e prazo "até 20 anos".
É ESTIMATIVA: a taxa e o limite finais saem da análise do parceiro. Não inclui IOF, avaliação do imóvel, registro em cartório nem seguros.
"""

TAXA_PARCEIRO_AM = 1.09   # % ao mês, "a partir de"
LTV_MAX = 0.60            # fração do valor do imóvel
CREDITO_MAX = 3_000_000   # teto de crédito da interface: teto comum de mercado (R$ 3 mi em Creditas e Neon); não é regra do parceiro
PRAZO_MAX_MESES = 240     # 20 anos
PRAZOS_ANOS = [5, 8, 10, 12, 15, 18, 20]
IMOVEL_MIN = 100_000
IMOVEL_MAX = 20_000_000
RECEBER_MIN = 50_000


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


def limite_credito(valor_imovel):
    return min(LTV_MAX * valor_imovel, CREDITO_MAX)


def receber_maximo(valor_imovel, saldo):
    return max(0.0, limite_credito(valor_imovel) - saldo)


def simular(valor_imovel, receber, saldo, meses, i):
    """Devolve parcela, total, juros e a relação crédito/imóvel. credito = o que você recebe + o saldo do financiamento que o novo crédito quita."""
    credito = receber + saldo
    parcela = pmt(credito, i, meses)
    total = parcela * meses
    return {
        "credito": credito,
        "parcela": parcela,
        "total": total,
        "juros": total - credito,
        "ltv": credito / valor_imovel if valor_imovel > 0 else 0.0,
        "limite": limite_credito(valor_imovel),
        "acima_limite": credito > limite_credito(valor_imovel) + 1e-9,
    }


def amortizacao_anual(credito, i, meses):
    """Como a dívida cai ano a ano na parcela fixa (Price): juros pagos, amortização e saldo devedor no fim de cada ano."""
    parcela = pmt(credito, i, meses)
    saldo = credito
    linhas = []
    restante = meses
    ano = 0
    while restante > 0:
        ano += 1
        juros = amortizado = 0.0
        for _ in range(min(12, restante)):
            j = saldo * i
            a = parcela - j
            saldo -= a
            juros += j
            amortizado += a
        restante -= 12
        linhas.append({"ano": ano, "juros": juros, "amortizacao": amortizado, "saldo": saldo if saldo > 0.005 else 0.0})
    return linhas


def comparar_quitacao(divida, taxa_divida_am, meses, i):
    """Mesma dívida e mesmo prazo: parcela e total na taxa da dívida (taxa_divida_am em fração ao mês) e no Home Equity (taxa i).
    juros_mes1 = o que a dívida cobra de juros só no primeiro mês."""
    atual = pmt(divida, taxa_divida_am, meses)
    he = pmt(divida, i, meses)
    return {
        "divida": divida,
        "parcela_atual": atual, "total_atual": atual * meses, "juros_mes1": divida * taxa_divida_am,
        "parcela_he": he, "total_he": he * meses,
        "economia_mes": atual - he, "economia_total": (atual - he) * meses,
    }


def receber_para_parcela(parcela_alvo, valor_imovel, saldo, meses, i, passo=5000):
    """Maior valor a receber (múltiplo de `passo`) cuja parcela cabe em parcela_alvo; 0 se nem o menor valor cabe."""
    bruto = valor_presente(parcela_alvo, i, meses) - saldo
    return max(0, int(bruto // passo) * passo)
