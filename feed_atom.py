"""Feed Atom 1.0 (feed.xml): atualizações do site e as taxas de referência do Banco Central mês a mês. Sem dado pessoal."""
import datetime
from xml.sax.saxutils import escape

import conteudo
import taxas_referencia as tr

DOMINIO = "https://homeequity.datalabglobal.com"
TAG = "tag:homeequity.datalabglobal.com,2026:"
MESES_NO_FEED = 6


def _iso(dia_mes_ano):
    d, m, a = dia_mes_ano.split("/")
    return "%s-%s-%sT00:00:00Z" % (a, m, d)


def _pct(v):
    return ("%.2f" % v).replace(".", ",") + "%"


def entradas():
    saida = []
    for i, (data, texto) in enumerate(conteudo.ATUALIZACOES):
        saida.append({"id": TAG + "atualizacao-" + _iso(data)[:10] + "-" + str(len(conteudo.ATUALIZACOES) - i),
                      "titulo": "Atualização de " + data, "data": _iso(data), "link": DOMINIO + "/atualizacoes", "resumo": texto})
    linhas = tr.ler()
    comparacao = [c for c in tr.CODIGOS_COMPARACAO]
    ultimas = {c: tr.serie(c, linhas)[-MESES_NO_FEED:] for c in comparacao}
    meses = sorted({r["mes"] for pontos in ultimas.values() for r in pontos}, reverse=True)
    for m in meses:
        partes = []
        for c in comparacao:
            r = next((x for x in ultimas[c] if x["mes"] == m), None)
            if r is not None:
                partes.append(tr.serie_def(c)["nome"].lower() + " " + _pct(tr.ao_mes(r)) + " ao mês")
        ano, mes = m.split("-")
        # o BCB publica o mês depois de fechado: usamos o primeiro dia do mês seguinte como data da entrada
        prox = datetime.date(int(ano) + (int(mes) == 12), int(mes) % 12 + 1, 1)
        saida.append({"id": TAG + "taxas-" + m, "titulo": "Taxas médias do Banco Central de " + tr.mes_extenso(m),
                      "data": prox.isoformat() + "T00:00:00Z", "link": DOMINIO + "/taxas-de-referencia",
                      "resumo": "Média das novas operações em " + tr.mes_extenso(m) + ": " + "; ".join(partes) + "."})
    saida.sort(key=lambda e: e["data"], reverse=True)
    return saida


def gerar(hoje=None):
    itens = entradas()
    atualizado = max(e["data"] for e in itens)  # a data da última entrada, não a de hoje: gerar o site de novo não atualiza o feed
    linhas = ['<?xml version="1.0" encoding="utf-8"?>', '<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="pt-BR">',
              "  <title>Home Equity — Datalab Global</title>",
              "  <subtitle>Atualizações do simulador e taxas de referência do Banco Central</subtitle>",
              '  <link href="' + DOMINIO + '/feed.xml" rel="self" type="application/atom+xml"/>',
              '  <link href="' + DOMINIO + '/" rel="alternate" type="text/html"/>',
              "  <id>" + TAG + "feed</id>", "  <updated>" + atualizado + "</updated>",
              "  <author><name>Datalab Global</name></author>"]
    for e in itens:
        linhas += ["  <entry>", "    <title>" + escape(e["titulo"]) + "</title>", '    <link href="' + e["link"] + '"/>',
                   "    <id>" + e["id"] + "</id>", "    <updated>" + e["data"] + "</updated>",
                   '    <summary type="text">' + escape(e["resumo"]) + "</summary>", "  </entry>"]
    linhas.append("</feed>")
    return "\n".join(linhas) + "\n"
