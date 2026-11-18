"""Conteúdo das páginas. Cada página tem texto próprio; nada de páginas quase iguais.

Regras: nenhum número que não venha de calculo.py, dos dados do Banco Central (dados/taxas_referencia.csv) ou de uma fonte citada; nenhum banco citado
nem ranking; sem prometer aprovação; tom calmo (a garantia é explicada sem alarmismo, mas sem esconder o risco). Os números dos textos são calculados
aqui, a partir de calculo.py, para não divergirem do simulador. Sem f-string aninhada (o CI roda Python 3.10).
"""
import calculo
import taxas_referencia as tr

# ---------- formatação ----------


def _milhar(texto):
    return texto.replace(",", "#").replace(".", ",").replace("#", ".")


def brl0(v):
    return "R$ " + _milhar(format(round(v), ",d"))


def pct(v):
    return _milhar(format(round(v, 2), ",.2f")) + "%"


def mes_curto(ano_mes):
    ano, mes = ano_mes.split("-")
    return ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"][int(mes) - 1] + "/" + ano


# ---------- blocos de HTML ----------


def h2(t):
    return "<h2>" + t + "</h2>\n"


def h3(t):
    return "<h3>" + t + "</h3>\n"


def p(t):
    return "<p>" + t + "</p>\n"


def ul(itens):
    return "<ul>" + "".join("<li>" + i + "</li>" for i in itens) + "</ul>\n"


def ol(itens):
    return "<ol>" + "".join("<li>" + i + "</li>" for i in itens) + "</ol>\n"


def aviso(t, ok=False):
    return '<div class="aviso' + (" ok" if ok else "") + '">' + t + "</div>\n"


def a(href, texto):
    return '<a href="' + href + '">' + texto + "</a>"


def tabela(cabecalho, linhas, legenda):
    topo = "".join('<th scope="col">' + c + "</th>" for c in cabecalho)
    # data-l: rótulo da coluna, usado no celular (o CSS empilha cada linha em um cartão; sem rolagem lateral)
    corpo = "".join("<tr>" + "".join('<td data-l="' + cabecalho[i] + '">' + c + "</td>" for i, c in enumerate(l)) + "</tr>" for l in linhas)
    return '<div class="tw"><table><caption>' + legenda + "</caption><thead><tr>" + topo + "</tr></thead><tbody>" + corpo + "</tbody></table></div>\n"


# ---------- números compartilhados ----------


def _ref():
    linhas = tr.ler()
    # defesa em profundidade: o ETL já filtra, mas se o CSV vier adulterado ou corrompido o site não pode ir ao ar com número absurdo
    for sd in tr.SERIES:
        ult = tr.ultima(sd["codigo"], linhas)
        lo, hi = sd["faixa"]
        if not (lo <= ult["valor"] <= hi):
            raise ValueError("taxa fora da faixa plausível na série %s: %s" % (sd["codigo"], ult["valor"]))
    ipca = tr.ultima(tr.CODIGO_IPCA, linhas)
    gar = tr.ultima(tr.CODIGO_GARANTIA_REAL, linhas)
    return {"ipca12m": ipca["valor"], "ipcaMes": mes_curto(ipca["mes"]), "garantiaRealAm": tr.ao_mes(gar), "garantiaRealMes": mes_curto(gar["mes"])}


def taxa_ref():
    return calculo.taxa_mensal(_ref()["ipca12m"])


def nota_taxa_maior(ref, i, imovel, receber, saldo, meses):
    """Mesmo texto que o simulador.js escreve na nota "E se a taxa for maior?" para o cenário informado."""
    r = calculo.simular(imovel, receber, saldo, meses, ref["garantiaRealAm"] / 100)
    return ("A estimativa usa a taxa de referência do parceiro (" + pct(calculo.TAXA_PARCEIRO_AM) + " a.m. + IPCA, cerca de " + pct(i * 100) +
            " a.m.). A média do Banco Central para crédito com garantia real é " + pct(ref["garantiaRealAm"]) + " a.m. (" + ref["garantiaRealMes"] +
            "): nessa taxa, a parcela do cenário acima seria de " + brl0(r["parcela"]) + ". A taxa final vem da análise.")


# ---------- amortização e "quitar dívida" (home): mesmos textos que o simulador.js escreve ----------
DIVIDAS = [("pessoal", "Crédito pessoal sem garantia"), ("cheque", "Cheque especial"), ("rotativo", "Cartão de crédito rotativo")]
DIVIDA_PADRAO = 60_000
DIVIDA_TIPO_PADRAO = "pessoal"


def amort_resumo(r, linhas):
    """Frase acima da tabela de amortização: quanto do primeiro ano é juros."""
    pago = r["parcela"] * 12
    j = linhas[0]["juros"]
    return ("No primeiro ano, " + brl0(j) + " dos " + brl0(pago) + " que você paga são juros (" + str(round(j / pago * 100)) +
            "%). A parcela é fixa: com o tempo ela amortiza mais a dívida e os juros caem.")


def amort_nota(ref):
    return ("A conta mantém o IPCA em " + pct(ref["ipca12m"]) + " ao ano (últimos 12 meses, " + ref["ipcaMes"] + ") e a parcela fixa. Se o IPCA mudar, a parcela e o saldo mudam. "
            "Não inclui IOF, avaliação do imóvel, registro nem seguros.")


def amort_linhas(linhas):
    """Linhas <tr> da tabela (o JS monta as mesmas)."""
    return "".join('<tr><th scope="row">' + str(x["ano"]) + "</th><td>" + brl0(x["juros"]) + "</td><td>" + brl0(x["amortizacao"]) + "</td><td>" + brl0(x["saldo"]) + "</td></tr>"
                   for x in linhas)


def amort_total(linhas, credito):
    juros = sum(x["juros"] for x in linhas)
    return '<tr><th scope="row">Total</th><td>' + brl0(juros) + "</td><td>" + brl0(credito) + "</td><td></td></tr>"


def quitar_cartoes(c, taxa_div_pct, anos, he_pct, custom=False):
    """Dois cartões: a dívida na taxa dela e no Home Equity (mesmo prazo). c vem de calculo.comparar_quitacao."""
    nome_a = ("Na taxa da sua dívida (" if custom else "Na taxa média (") + pct(taxa_div_pct) + " a.m.)"
    a_ = ('<div class="alt"><h3>' + nome_a + '</h3><div class="p num">' + brl0(c["parcela_atual"]) + '</div><div class="d">Só de juros: ' + brl0(c["juros_mes1"]) +
          " no 1º mês<br>Total em " + str(anos) + " anos: " + brl0(c["total_atual"]) + "</div></div>")
    if c["economia_mes"] > 0:
        dest = '<span class="dn">' + brl0(c["economia_mes"]) + " a menos por mês</span>"
    else:
        dest = '<span class="up">sem redução de parcela nesta conta</span>'
    b = ('<div class="alt cur"><h3>No Home Equity (' + pct(he_pct) + ' a.m.)</h3><div class="p num">' + brl0(c["parcela_he"]) + '</div><div class="d">Total em ' + str(anos) +
         " anos: " + brl0(c["total_he"]) + "<br>" + dest + "</div></div>")
    return a_ + b


def quitar_texto(c, anos):
    if c["economia_mes"] > 0:
        return ("Trocar esta dívida reduziria a parcela em " + brl0(c["economia_mes"]) + " por mês e o total pago em cerca de " + brl0(c["economia_total"]) +
                ", com a mesma duração (" + str(anos) + " anos). Avaliação, registro e seguros não entram na conta e reduzem essa economia.")
    return "Com esta taxa, o Home Equity não reduz a parcela da dívida. Peça o CET da proposta e compare antes de decidir."


# ---------- perguntas frequentes (home) ----------
FAQ = [
    ("Posso continuar morando no imóvel?",
     "Sim. No Home Equity o imóvel fica como garantia, mas você continua usando: morando, alugando ou mantendo o negócio nele, conforme o contrato. "
     "O que muda é o registro da garantia na matrícula, que sai quando a dívida é quitada. Veja " + a("/garantia-do-imovel", "como funciona a garantia") + "."),
    ("Posso usar um imóvel que ainda está financiado?",
     "Em geral, sim, conforme a instituição: o novo crédito quita o saldo do financiamento e libera a diferença para você. Por isso o simulador tem a opção "
     "\"Ainda financiado\": o saldo entra no total do crédito e conta para o limite de 60% do valor do imóvel (teto de R$ 3 milhões de crédito nesta ferramenta)."),
    ("Por que a parcela muda com o IPCA?",
     "Porque a taxa divulgada pelo parceiro é \"a partir de 1,09% ao mês mais IPCA\": além dos juros, o saldo é atualizado pela inflação. O simulador usa o IPCA dos últimos 12 meses "
     "e o mantém constante, então a parcela real pode ficar acima ou abaixo da estimativa, conforme a inflação dos próximos anos."),
    ("Quanto tempo leva até o dinheiro cair na conta?",
     "Não há um prazo único: depende da análise de crédito, da avaliação do imóvel, da análise jurídica e do registro da garantia em cartório. Cada instituição informa o seu prazo na proposta."),
    ("O que acontece se eu atrasar as parcelas?",
     "Atrasos geram encargos previstos no contrato e, se a dívida não for regularizada, a lei prevê um procedimento de cobrança que pode chegar à venda do imóvel dado em garantia. "
     "Por isso vale escolher uma parcela que caiba com folga. Detalhes em " + a("/garantia-do-imovel", "Garantia do imóvel") + "."),
    ("A simulação vale como proposta?",
     "Não. É uma estimativa feita com taxa de referência, sem consultar você nem o imóvel. A taxa, o limite e o prazo finais saem da análise de crédito e da avaliação do imóvel."),
]


# ---------- páginas ----------


def corpo_como_funciona(ctx):
    r = calculo.simular(800_000, 250_000, 0, 180, taxa_ref())
    return (
        p("Home Equity é um crédito em que você oferece um imóvel como garantia e recebe dinheiro em parcelas fixas. Como a instituição tem a garantia, os juros costumam ser "
          "bem menores que os do crédito pessoal sem garantia ou do cartão. Você continua usando o imóvel."
          )
        + h2("O que você informa e o que o crédito libera")
        + p("O parceiro de crédito divulga que o Home Equity libera <b>até 60% do valor do imóvel</b>, em <b>até 20 anos</b>, com taxa a partir de <b>1,09% ao mês mais IPCA</b>. "
            "O imóvel pode ser residencial, comercial ou terreno, e pode estar financiado ou ser de terceiro, conforme a instituição.")
        + p("Exemplo do simulador: imóvel de " + brl0(800_000) + ", você quer receber " + brl0(250_000) + " em 15 anos. O crédito usa " + str(round(r["ltv"] * 100)) +
            "% do valor do imóvel, a parcela estimada é de " + brl0(r["parcela"]) + " por mês e o total ao final é de " + brl0(r["total"]) + ".")
        + h2("Passo a passo")
        + ol([
            "<b>Simulação.</b> Você vê a estimativa aqui, sem cadastro.",
            "<b>Pedido e análise de crédito.</b> Você preenche o formulário de um parceiro de crédito; ele analisa renda, histórico e endividamento e responde com a proposta.",
            "<b>Documentos.</b> Seus documentos e os do imóvel, como a matrícula atualizada.",
            "<b>Avaliação e análise jurídica.</b> A instituição avalia o imóvel (o valor dela pode ser diferente do preço de compra) e confere a situação legal dele.",
            "<b>Contrato e registro.</b> Você assina o contrato e a garantia é registrada em cartório.",
            "<b>Liberação.</b> O dinheiro é liberado e você começa a pagar as parcelas.",
        ])
        + h2("Para que as pessoas usam")
        + ul([
            "Trocar dívidas caras (cartão, cheque especial, empréstimos sem garantia) por uma parcela de juro menor, em prazo maior.",
            "Capital de giro ou investimento no próprio negócio.",
            "Reforma ou uma despesa grande e planejada.",
        ])
        + aviso("Prazo maior deixa a parcela menor, mas o total pago cresce. O simulador mostra as duas coisas lado a lado no <b>Raio-X da decisão</b>.", ok=True)
        + p("Veja também " + a("/garantia-do-imovel", "como funciona a garantia") + ", " + a("/custos-alem-dos-juros", "os custos além dos juros") + " e " + a("/metodologia", "como calculamos") + ".")
    )


def corpo_garantia(ctx):
    return (
        p("A garantia é o que torna o Home Equity mais barato: a instituição corre menos risco e cobra juros menores. Entender como ela funciona antes de pedir ajuda a escolher "
          "uma parcela que caiba com folga. Este texto é informativo e não substitui a leitura do contrato nem a orientação de um advogado.")
        + h2("O que muda para você")
        + ul([
            "Você continua com a posse e o uso do imóvel: pode morar, alugar ou manter o negócio nele, conforme o contrato.",
            "A propriedade fica em garantia com a instituição (veja abaixo), mas a posse e o uso continuam com você, e a garantia fica registrada na matrícula.",
        ])
        + h2("O que fica registrado")
        + p("A modalidade mais comum é a <b>alienação fiduciária</b> (Lei nº 9.514/1997): a propriedade fica em garantia com a instituição enquanto a dívida existe, e o registro é feito em cartório. "
            "Quando você quita a dívida, a instituição fornece o termo de quitação e você faz o cancelamento do registro. A forma exata (inclusive quanto a imóvel de terceiro ou ainda financiado) é definida no contrato de cada instituição.")
        + h2("Se as parcelas deixarem de ser pagas")
        + p("Atrasos geram encargos previstos no contrato. Se a dívida continuar sem pagamento, a lei prevê um procedimento: você é notificado, tem um prazo para regularizar e, "
            "não havendo pagamento, a propriedade é consolidada na instituição, que leva o imóvel a leilão. Se o valor arrecadado superar a dívida e os custos, a diferença é devolvida a você. "
            "É um caminho de último recurso, e a conversa com a instituição antes do atraso costuma abrir alternativas, como renegociar o prazo.")
        + h2("Como ficar mais tranquilo")
        + ul([
            "Escolha uma parcela que caiba com folga no seu orçamento; use a <b>parcela confortável</b> do Raio-X do simulador como referência sua.",
            "Lembre que a parcela é atualizada pelo IPCA: reserve uma margem para ela variar.",
            "Se a renda é variável, pense numa reserva de alguns meses de parcela.",
            "Leia o contrato inteiro, em especial as regras de atraso, de quitação antecipada e de seguros.",
        ])
        + aviso("Vender ou alugar o imóvel dado em garantia, ou fazer outra operação sobre ele, normalmente exige falar com a instituição antes. Confira o que o contrato prevê.")
        + p("Veja também " + a("/custos-alem-dos-juros", "os custos além dos juros") + " e " + a("/quando-nao-vale-a-pena", "quando o Home Equity não vale a pena") + ".")
    )


def corpo_custos(ctx):
    i = taxa_ref()
    p15 = calculo.simular(800_000, 250_000, 0, 180, i)
    return (
        p("O simulador mostra a parcela e o total com juros e IPCA. A proposta real pode ter outros custos, e é por isso que ela traz o <b>CET (Custo Efetivo Total)</b>: "
          "a taxa que reúne juros e despesas da operação. Peça o CET e compare propostas por ele, não só pela taxa de juros.")
        + h2("O que pode entrar além dos juros")
        + ul([
            "<b>IOF</b>, o imposto sobre operações de crédito.",
            "<b>Avaliação do imóvel</b>, feita pela instituição.",
            "<b>Certidões e registro</b> da garantia em cartório.",
            "<b>Seguros</b>, como o de vida e o do imóvel, quando exigidos pela instituição.",
            "<b>Tarifas</b> de cadastro ou de análise, quando previstas.",
        ])
        + p("Quais dessas despesas existem, e quanto custam, varia de uma instituição para outra. Este simulador <b>não as inclui</b>: por isso a parcela mostrada é uma estimativa.")
        + h2("A atualização pelo IPCA")
        + p("A taxa de referência do parceiro é composta: 1,09% ao mês mais a inflação medida pelo IPCA. Com o IPCA de " + pct(_ref()["ipca12m"]) + " em 12 meses (" + _ref()["ipcaMes"] +
            "), a taxa de referência fica em torno de " + pct(i * 100) + " ao mês. Se a inflação subir, a parcela sobe; se cair, a parcela cai. "
            "Para " + brl0(250_000) + " em 15 anos, a parcela estimada é de " + brl0(p15["parcela"]) + " hoje.")
        + h2("Exemplo de como o prazo pesa")
        + tabela(["Prazo", "Parcela estimada", "Total ao final", "Juros no total"],
                 [[str(a_) + " anos", brl0(calculo.simular(800_000, 250_000, 0, a_ * 12, i)["parcela"]), brl0(calculo.simular(800_000, 250_000, 0, a_ * 12, i)["total"]),
                   brl0(calculo.simular(800_000, 250_000, 0, a_ * 12, i)["juros"])] for a_ in (5, 10, 15, 20)],
                 "Receber " + brl0(250_000) + " com imóvel de " + brl0(800_000) + ", taxa de referência " + pct(i * 100) + " ao mês, sem IOF e sem tarifas.")
        + p("Prazo maior deixa a parcela menor e aumenta o total pago. Escolher entre os dois depende do que cabe no seu orçamento e do que importa para você.")
    )


def corpo_comparar(ctx):
    linhas = tr.ler()
    i_ref = taxa_ref()
    itens = [("Home Equity (referência do parceiro)", i_ref * 100)]
    for c in tr.CODIGOS_COMPARACAO:
        u = tr.ultima(c, linhas)
        itens.append((tr.serie_def(c)["nome"] + " (média do mercado)", tr.ao_mes(u)))
    base = 100_000
    meses = 60
    tab = []
    for nome, taxa in itens:
        pm = calculo.pmt(base, taxa / 100, meses)
        tab.append([nome, pct(taxa), brl0(pm), brl0(pm * meses - base)])
    return (
        p("O Home Equity costuma ter juros mensais bem menores que os do crédito sem garantia. A comparação abaixo usa a mesma conta para todos: tomar " + brl0(base) + " em " + str(meses) +
          " meses, com parcela fixa e a taxa de cada modalidade.")
        + tabela(["Modalidade", "Juros ao mês", "Parcela", "Juros no total"], tab,
                 "Mesmo valor e mesmo prazo, só mudando a taxa. Médias do Banco Central (" + mes_curto(tr.ultima(29976, linhas)["mes"]) + "); a taxa de referência do Home Equity é a do parceiro mais IPCA.")
        + aviso("É uma comparação de taxas, não de ofertas. Na prática o crédito sem garantia costuma ter prazo e valor máximos menores, e o Home Equity pode ter custos de avaliação e registro. "
                "Compare o CET de cada proposta antes de decidir.")
        + h2("O que a garantia muda")
        + ul([
            "<b>Cartão rotativo e cheque especial</b> são os mais caros e feitos para uso curto. Dívida neles por meses sai muito mais cara.",
            "<b>Crédito pessoal sem garantia</b> não exige patrimônio em garantia, mas cobra juros mais altos.",
            "<b>Crédito com garantia real</b> (imóvel ou veículo) tem juros menores, em troca de colocar um bem em garantia.",
        ])
        + p("Se o objetivo é trocar uma dívida cara, o simulador de Home Equity mostra quanto ficaria a parcela; o " + a("/quando-nao-vale-a-pena", "texto sobre quando não vale a pena")
            + " ajuda a pesar o outro lado.")
    )


def corpo_quando_nao(ctx):
    return (
        p("O Home Equity pode ser uma opção boa, e há situações em que vale pensar duas vezes. Estas são as perguntas que a gente faria antes de pedir.")
        + h2("Quando vale pensar duas vezes")
        + ul([
            "<b>A parcela só cabe com aperto.</b> Se a parcela estimada passa do que você consegue pagar com folga, reduza o valor, aumente o prazo ou espere. Use o Raio-X do simulador.",
            "<b>A renda é incerta.</b> Com a garantia em jogo, uma queda de renda pesa mais; uma reserva de alguns meses de parcela ajuda.",
            "<b>O dinheiro é para um gasto que não se paga.</b> Usar uma dívida de 15 anos para uma despesa de consumo de curto prazo costuma sair caro no total.",
            "<b>O valor é pequeno.</b> Avaliação, registro e seguros pesam mais em valores baixos; compare o CET com o de outras opções.",
            "<b>Existe crédito mais barato disponível.</b> Consignado, refinanciar o financiamento atual ou pagar uma dívida com recursos próprios podem custar menos.",
            "<b>A situação do imóvel é complexa.</b> Pendências na matrícula, imóvel de mais de um dono ou inventário podem atrasar ou impedir a operação.",
        ])
        + h2("Quando pode fazer sentido")
        + ul([
            "Trocar dívidas de juro muito alto por uma parcela fixa e menor, com prazo que você consegue acompanhar.",
            "Financiar um projeto ou um negócio com retorno esperado maior que o custo do crédito.",
            "Reunir várias dívidas em uma só, com um orçamento organizado depois.",
        ])
        + aviso("Não oferecemos recomendação financeira personalizada. O simulador mostra números; a decisão depende da sua situação, e em dúvida vale conversar com alguém de confiança ou com um profissional.", ok=True)
        + p("Antes de decidir, veja " + a("/custos-alem-dos-juros", "os custos além dos juros") + " e " + a("/garantia-do-imovel", "como funciona a garantia") + ".")
    )


def corpo_taxas(ctx):
    linhas = tr.ler()
    ref = []
    for s in tr.SERIES:
        u = tr.ultima(s["codigo"], linhas)
        if not u:
            continue
        valor = pct(u["valor"]) + (" ao mês" if s["unidade"] == "am" else " ao ano")
        mensal = pct(tr.ao_mes(u)) + " ao mês" if s["codigo"] != tr.CODIGO_IPCA else "—"
        ref.append([s["nome"], mes_curto(u["mes"]), valor, mensal, '<a href="' + tr.url_fonte(s["codigo"]) + '" rel="noopener">SGS ' + str(s["codigo"]) + "</a>"])
    i = taxa_ref()
    return (
        p("O simulador usa duas famílias de taxa: a <b>taxa do parceiro</b>, para estimar a parcela, e as <b>médias do Banco Central</b>, para comparar e para o aviso \"e se a taxa for maior?\".")
        + h2("Taxa de referência do Home Equity")
        + p("Segundo o parceiro de crédito, o Home Equity tem taxa a partir de <b>1,09% ao mês mais IPCA</b>. Com o IPCA em 12 meses de " + pct(_ref()["ipca12m"]) + " (" + _ref()["ipcaMes"] +
            "), a taxa mensal de referência fica em <b>" + pct(i * 100) + "</b>: (1 + 1,09%) x (1 + IPCA mensal) − 1. É a melhor condição divulgada, e a proposta real pode ser maior.")
        + h2("Médias do Banco Central")
        + tabela(["Série", "Mês", "Valor da série", "Em % ao mês", "Fonte"], ref,
                 "Taxas médias das novas operações de crédito livre de pessoas físicas e IPCA. Fonte: Banco Central do Brasil (SGS), licença ODbL.")
        + p("Atualizamos esses números toda semana, direto da API do Banco Central. Os dados em CSV estão em " + a("/dados/taxas-referencia.csv", "/dados/taxas-referencia.csv") + ".")
        + h2("Limites desses números")
        + ul([
            "A série de <b>crédito com garantia real</b> mistura imóvel e veículo: o Banco Central não separa Home Equity de crédito com veículo em garantia. Por isso ela é uma referência, não a taxa do Home Equity.",
            "Média é média: a sua taxa pode ser menor ou maior, conforme a análise de crédito, o valor, o prazo e o imóvel.",
            "As taxas do Banco Central são de operações já contratadas no mês indicado, e saem com defasagem.",
            "Nenhuma dessas taxas é oferta de crédito.",
        ])
    )


def corpo_metodologia(ctx):
    i = taxa_ref()
    r = calculo.simular(800_000, 250_000, 0, 180, i)
    return (
        p("Em poucas linhas: o simulador calcula a parcela fixa de um empréstimo, com a taxa de referência do parceiro mais IPCA, sobre o crédito que você pediria. Aqui está cada parte da conta.")
        + h2("A conta")
        + ol([
            "<b>Crédito total</b> = valor que você quer receber + saldo devedor do financiamento, se o imóvel ainda estiver financiado (o novo crédito quita esse saldo).",
            "<b>Taxa mensal</b> = (1 + 1,09%) x (1 + IPCA mensal) − 1. O IPCA mensal é o equivalente composto do IPCA de 12 meses do IBGE, via Banco Central (SGS 13522), mantido constante.",
            "<b>Parcela</b> = crédito x i / (1 − (1 + i)^−n), com i a taxa mensal e n o prazo em meses (tabela Price, parcela fixa).",
            "<b>Total ao final</b> = parcela x n. <b>Juros no total</b> = total − crédito.",
            "<b>Limite</b> = 60% do valor do imóvel, conforme divulgado pelo parceiro, e no máximo R$ 3 milhões de crédito por simulação (teto desta ferramenta). O saldo devedor conta para esse limite.",
        ])
        + p("Exemplo: imóvel de " + brl0(800_000) + ", receber " + brl0(250_000) + ", 180 meses, taxa " + pct(i * 100) + " ao mês. Parcela de " + brl0(r["parcela"]) +
            " e total de " + brl0(r["total"]) + ".")
        + h2("O que a conta não inclui")
        + ul([
            "IOF, tarifas, avaliação do imóvel, registro em cartório e seguros (veja " + a("/custos-alem-dos-juros", "custos além dos juros") + ").",
            "Variação futura do IPCA: usamos o valor dos últimos 12 meses, parado.",
            "Análise de crédito, valor de avaliação do imóvel e limite de cada instituição, que definem a oferta real.",
        ])
        + h2("O Raio-X da decisão")
        + p("A \"parcela confortável\" é um número que você informa. O simulador só compara: diz quanto a parcela estimada fica acima ou abaixo dele e mostra duas alternativas (receber menos e outro prazo) com a mesma taxa. "
            "Ele <b>não avalia capacidade de pagamento</b> nem decide por você.")
        + h2("Conferência")
        + p("O código do simulador é testado automaticamente: a conta do navegador é comparada com a conta de referência em Python, em dezenas de cenários, a cada alteração do site.")
    )


def corpo_sobre(ctx):
    return (
        p("Datalab Global é uma marca de " + ctx["razao"] + ", CNPJ " + ctx["cnpj"] + ". Este simulador existe para você ver a parcela e o custo do Home Equity antes de pedir uma proposta.")
        + h2("Quem analisa o seu pedido")
        + p("O pedido é analisado por um parceiro de crédito. É ele quem faz a análise, a avaliação do imóvel e a proposta. A Datalab Global não concede crédito e não é banco.")
        + h2("O que fazemos")
        + ul([
            "Mostramos a parcela e o total estimados, com a conta e as fontes abertas (veja " + a("/metodologia", "Metodologia") + ").",
            "Mostramos as taxas do Banco Central ao lado, para você comparar tipos de crédito (veja " + a("/taxas-de-referencia", "Taxas do Banco Central") + ").",
            "Não coletamos dado pessoal neste site: o que você digita no simulador fica no seu navegador.",
            "Não fazemos ranking de bancos nem indicamos instituição específica.",
            "Não garantimos aprovação: ela depende da análise do parceiro.",
        ])
        + h2("Por que este simulador existe")
        + p("Crédito com garantia pede uma decisão grande, e a parcela é só uma parte dela. Montamos o simulador para mostrar primeiro o custo e as alternativas, e só depois o caminho para o pedido.")
        + h2("Contato")
        + p('E-mail: <a href="mailto:' + ctx["email"] + '">' + ctx["email"] + "</a>. Se encontrar um número errado ou uma informação desatualizada, escreva: corrigimos e registramos em "
            + a("/atualizacoes", "Atualizações") + ".")
    )


ATUALIZACOES = [
    ("18/11/2026", "Simulador de Home Equity publicado em homeequity.datalabglobal.com, com parcela estimada, Raio-X da decisão, comparação de custo mensal entre tipos de crédito e guias sobre garantia, custos e taxas."),
]


def corpo_atualizacoes(ctx):
    itens = "".join("<li><b>" + d + "</b> — " + t + "</li>" for d, t in ctx["atualizacoes"])
    return p("Registro das mudanças relevantes: conferências, correções e novas páginas. A mais recente aparece primeiro.") + "<ul>" + itens + "</ul>\n"


def _secoes(secoes):
    return "".join(h2(t) + "".join(p(x) for x in ps) for t, ps in secoes)


def corpo_privacidade(ctx):
    return (
        p("Esta Política explica como este site trata dados pessoais, em conformidade com a Lei Geral de Proteção de Dados (Lei nº 13.709/2018). Última atualização: " + ctx["atualizado"] + ".")
        + _secoes([
            ("1. Dados que este site coleta",
             ["Nenhum dado pessoal é pedido neste site. Os valores que você digita no simulador ficam no seu navegador. Se você escrever para " + ctx["email"] +
              ", guardamos o seu e-mail e o conteúdo da mensagem para responder."]),
            ("2. Medição de uso",
             ["Usamos o Umami, que não usa cookies e não identifica você. Ele conta visitas e alguns eventos (usar a simulação, abrir a tela de confirmação, seguir para o parceiro e copiar o link), "
              "com o valor a receber e o prazo simulados. A hospedagem (Cloudflare) pode tratar o endereço IP para entregar o site e proteger contra ataques."]),
            ("3. Ao seguir para o parceiro",
             ["Ao clicar em continuar para o parceiro, você sai deste site e abre o formulário de um parceiro de crédito. Este site não envia a ele os valores da simulação. "
              "Os dados que você digitar lá (documentos, renda, dados do imóvel) são tratados pelo parceiro, conforme a política dele, e não passam por este site."]),
            ("4. Bases legais",
             ["Tratamos dados com base no legítimo interesse (segurança e melhoria do site), no cumprimento de obrigações legais e, quando for o caso, no seu consentimento."]),
            ("5. Compartilhamento",
             ["Não vendemos dados. Compartilhamos o mínimo com provedores que operam o site (hospedagem e medição), sob contrato."]),
            ("6. Seus direitos",
             ["Você pode pedir confirmação de tratamento, acesso, correção, eliminação e revogação de consentimento, a qualquer momento, pelo e-mail " + ctx["email"] + "."]),
            ("7. Cookies", ["Este site não usa cookies de publicidade nem de rastreamento."]),
            ("8. Contato e alterações",
             ["O canal para assuntos de privacidade é " + ctx["email"] + ". Esta Política pode ser atualizada; vale a versão publicada nesta página. Responsável: " + ctx["razao"] + ", CNPJ " + ctx["cnpj"] + "."]),
        ])
    )


def corpo_termos(ctx):
    return (
        p("Estes Termos regulam o uso deste site. Ao usar o site, você concorda com as condições abaixo. Última atualização: " + ctx["atualizado"] + ".")
        + _secoes([
            ("1. O que é este site",
             ["Um simulador de Home Equity mantido por " + ctx["razao"] + " (marca Datalab Global). Ele mostra estimativas e leva você ao formulário de um parceiro de crédito, que é quem analisa o pedido."]),
            ("2. A simulação não é proposta de crédito",
             ["Os números são estimativas informativas, feitas com taxas de referência. Não são oferta, promessa de crédito nem recomendação financeira. "
              "A aprovação, o valor, a taxa e as condições finais dependem da análise de crédito e da avaliação do imóvel pelo parceiro."]),
            ("3. Uso permitido",
             ["Você pode usar o site para fins lícitos. É proibido tentar acessar áreas restritas, sobrecarregar a infraestrutura ou extrair dados em massa de forma automatizada sem autorização."]),
            ("4. Propriedade intelectual",
             ["Marca, layout e textos pertencem aos seus titulares. Os dados das taxas do Banco Central seguem a licença da fonte (ODbL 1.0)."]),
            ("5. Limitação de responsabilidade",
             ["O site é oferecido no estado em que se encontra. Fazemos esforços razoáveis para mantê-lo correto e disponível, mas não garantimos ausência de falhas. A relação de crédito é entre você e o parceiro."]),
            ("6. Alterações e contato", ["Podemos atualizar estes Termos; vale a versão publicada nesta página. Dúvidas: " + ctx["email"] + "."]),
        ])
    )


# slug, título (≤ 60 caracteres), h1, descrição, corpo, cartão na home (texto) ou None
PAGINAS = [
    dict(slug="como-funciona", cartao="Como funciona o Home Equity", title="Como funciona o Home Equity, passo a passo",
         h1="Como funciona o Home Equity, passo a passo",
         desc="Entenda o crédito com imóvel em garantia: quanto libera, em quanto tempo se paga, o que o parceiro analisa e as etapas até receber.", corpo=corpo_como_funciona),
    dict(slug="garantia-do-imovel", cartao="A garantia do imóvel", title="Garantia do imóvel no Home Equity: como funciona",
         h1="Como funciona a garantia do imóvel",
         desc="O que muda quando o imóvel fica como garantia: uso, registro em cartório, o que acontece em caso de atraso e como escolher uma parcela com folga.", corpo=corpo_garantia),
    dict(slug="custos-alem-dos-juros", cartao="Custos além dos juros", title="Custos do Home Equity além dos juros",
         h1="Custos do Home Equity além dos juros",
         desc="IOF, avaliação, registro, seguros e atualização pelo IPCA: o que pode somar à parcela e por que pedir o CET da proposta.", corpo=corpo_custos),
    dict(slug="home-equity-ou-outro-credito", cartao="Home Equity ou outro crédito", title="Home Equity ou outro crédito: compare o custo mensal",
         h1="Home Equity ou outro crédito: compare o custo mensal",
         desc="A mesma conta para Home Equity, crédito pessoal, cheque especial e cartão rotativo, com as médias do Banco Central.", corpo=corpo_comparar),
    dict(slug="quando-nao-vale-a-pena", cartao="Quando não vale a pena", title="Quando o Home Equity não vale a pena (e quando pode valer)",
         h1="Quando o Home Equity não vale a pena",
         desc="Situações em que vale pensar duas vezes antes de dar o imóvel em garantia, e as em que o crédito pode fazer sentido.", corpo=corpo_quando_nao),
    dict(slug="taxas-de-referencia", cartao="Taxas do Banco Central", title="Taxas de referência do Home Equity e do Banco Central",
         h1="Taxas de referência: de onde vêm os números",
         desc="A taxa do parceiro (1,09% ao mês mais IPCA) e as médias do Banco Central usadas no simulador, com o mês e a fonte de cada uma.", corpo=corpo_taxas),
    dict(slug="metodologia", cartao=None, menu="Metodologia", title="Metodologia: como calculamos o Home Equity",
         h1="Metodologia: como calculamos a parcela", desc="A conta do simulador, passo a passo, o que ela não inclui e como o Raio-X compara cenários.", corpo=corpo_metodologia),
    dict(slug="sobre", cartao=None, menu="Sobre", title="Sobre a Datalab Global e este simulador",
         h1="Sobre este simulador", desc="Quem mantém o simulador de Home Equity, o que fazemos e o que não fazemos.", corpo=corpo_sobre),
    dict(slug="atualizacoes", cartao=None, menu="Atualizações", title="Atualizações do simulador de Home Equity",
         h1="Atualizações do simulador", desc="Registro das mudanças e correções do simulador de Home Equity.", corpo=corpo_atualizacoes, guia=False),
    dict(slug="privacidade", cartao=None, menu="Privacidade", title="Política de Privacidade", h1="Política de Privacidade",
         desc="Como o simulador de Home Equity trata dados pessoais (LGPD).", corpo=corpo_privacidade, guia=False),
    dict(slug="termos", cartao=None, menu="Termos de uso", title="Termos de Uso", h1="Termos de Uso",
         desc="Condições de uso do simulador de Home Equity.", corpo=corpo_termos, guia=False),
]
