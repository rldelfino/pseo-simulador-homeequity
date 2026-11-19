"""Gera o site estático do simulador de Home Equity (crédito com imóvel em garantia) da Datalab Global.

Saída em paginas_seo/ (publicada no Cloudflare Pages, sem build). O CSS é escrito à mão em src/estilo.css e copiado para paginas_seo/styles.css.
Uso: python gerador_homeequity.py [pasta_de_saida]

Regras do projeto: poucas páginas, cada uma com conteúdo próprio (nada de grade de páginas quase idênticas); nenhum dado pessoal; medição só com
Umami (sem cookies). O texto das páginas fica em conteudo.py.
"""
import datetime
import hashlib
import json
import os
import re
import shutil
import sys

import calculo
import conteudo
import feed_atom
import indexnow
import layout
import taxas_referencia as tr

AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA_PADRAO = os.path.join(AQUI, "paginas_seo")

DOMINIO = "https://homeequity.datalabglobal.com"
HUB = "https://www.datalabglobal.com"
UMAMI_ID = "ba3c0b88-59e8-47dd-866d-0b05e5e7dae9"  # mesmo site do Umami dos irmãos (plano gratuito = 1 site); separar por hostname = homeequity.datalabglobal.com
RAZAO_SOCIAL = "Satori Soluções Comerciais LTDA"
CNPJ = "63.998.502/0001-73"
EMAIL = "contato@datalabglobal.com"
# Link de conversão do parceiro (formulário de Home Equity). Fica só no código do botão da tela de confirmação.
LINK_PARCEIRO = "https://proposta.api.br/f/ffcdc9ea-0181-46ae-b12d-874844478349"

MANIFESTO_PADRAO = os.path.join(AQUI, "dados", "datas_paginas.json")
DATA_SENTINELA = datetime.date(2000, 1, 1)

HOME_TITLE = "Home Equity: simule a parcela com seu imóvel em garantia"
HOME_DESC = ("Simule o Home Equity (crédito com imóvel em garantia): veja a parcela e o custo total estimados, até 60% do valor do imóvel e até 20 anos. "
             "Grátis e sem cadastro.")

PAGINAS_INDEXAVEIS = ["/"] + ["/" + pg["slug"] for pg in conteudo.PAGINAS]

CSP = (
    "default-src 'self'; "
    "script-src 'self' https://cloud.umami.is; "
    "style-src 'self'; "
    "img-src 'self' data:; "
    "font-src 'self'; "
    "connect-src 'self' https://cloud.umami.is https://api-gateway.umami.dev https://gateway.umami.is; "
    "frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'; upgrade-insecure-requests"
)

HEADERS = """/*
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Strict-Transport-Security: max-age=31536000; includeSubDomains
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: geolocation=(), camera=(), microphone=(), payment=(), usb=(), interest-cohort=()
  Cross-Origin-Opener-Policy: same-origin
  Content-Security-Policy: @@CSP@@

/styles.css
  Cache-Control: public, max-age=31536000, immutable

/calculo.js
  Cache-Control: public, max-age=3600, must-revalidate

/simulador.js
  Cache-Control: public, max-age=3600, must-revalidate

/menu.js
  Cache-Control: public, max-age=3600, must-revalidate

/og-image.png
  Cache-Control: public, max-age=86400, must-revalidate

/fonts/*
  Cache-Control: public, max-age=31536000, immutable
"""

CALCULO_JS = """/* GERADO por gerador_homeequity.py a partir de calculo.py e dados/taxas_referencia.csv. Não edite à mão.
   Mesma conta de calculo.py (os testes comparam os dois). */
(function (root) {
  'use strict';
  var TAXA_PARCEIRO_AM = @@TAXA_PARCEIRO@@;
  var LTV_MAX = @@LTV@@;
  var CREDITO_MAX = @@CREDITO_MAX@@;
  var PRAZO_MIN_ANOS = @@PRAZO_MIN@@;
  var PRAZO_MAX_ANOS = @@PRAZO_MAX@@;
  var IMOVEL_MIN = @@IMOVEL_MIN@@;
  var IMOVEL_MAX = @@IMOVEL_MAX@@;
  var RECEBER_MIN = @@RECEBER_MIN@@;
  // Referências do Banco Central (médias de mercado, não oferta): IPCA em 12 meses e taxa média de crédito com garantia real (% ao mês).
  var REF = @@REFERENCIAS@@;

  function ipcaMensal(ipca12m) { return Math.pow(1 + ipca12m / 100, 1 / 12) - 1; }
  function taxaMensal(ipca12m) { return (1 + TAXA_PARCEIRO_AM / 100) * (1 + ipcaMensal(ipca12m)) - 1; }
  function pmt(principal, i, n) { return i === 0 ? principal / n : principal * i / (1 - Math.pow(1 + i, -n)); }
  function valorPresente(parcela, i, n) { return i === 0 ? parcela * n : parcela * (1 - Math.pow(1 + i, -n)) / i; }
  function limiteCredito(imovel) { return Math.min(LTV_MAX * imovel, CREDITO_MAX); }

  function simular(imovel, receber, saldo, meses, i) {
    var credito = receber + saldo;
    var parcela = pmt(credito, i, meses);
    var total = parcela * meses;
    return { credito: credito, parcela: parcela, total: total, juros: total - credito, ltv: imovel > 0 ? credito / imovel : 0,
             limite: limiteCredito(imovel), acimaLimite: credito > limiteCredito(imovel) + 1e-9 };
  }

  function receberParaParcela(parcelaAlvo, saldo, meses, i, passo) {
    var bruto = valorPresente(parcelaAlvo, i, meses) - saldo;
    return Math.max(0, Math.floor(bruto / passo) * passo);
  }

  function amortizacaoAnual(credito, i, meses) {
    var parcela = pmt(credito, i, meses), saldo = credito, restante = meses, ano = 0, linhas = [];
    while (restante > 0) {
      ano += 1;
      var juros = 0, amortizado = 0, n = Math.min(12, restante);
      for (var k = 0; k < n; k++) { var j = saldo * i, a = parcela - j; saldo -= a; juros += j; amortizado += a; }
      restante -= 12;
      linhas.push({ ano: ano, juros: juros, amortizacao: amortizado, saldo: saldo > 0.005 ? saldo : 0 });
    }
    return linhas;
  }

  function compararQuitacao(divida, taxaDividaAm, meses, i) {
    var atual = pmt(divida, taxaDividaAm, meses), he = pmt(divida, i, meses);
    return { divida: divida, parcelaAtual: atual, totalAtual: atual * meses, jurosMes1: divida * taxaDividaAm,
             parcelaHe: he, totalHe: he * meses, economiaMes: atual - he, economiaTotal: (atual - he) * meses };
  }

  function brl(v) { return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(Math.round(v)); }
  function pct(v) { return v.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + '%'; }

  var api = { TAXA_PARCEIRO_AM: TAXA_PARCEIRO_AM, LTV_MAX: LTV_MAX, CREDITO_MAX: CREDITO_MAX, PRAZO_MIN_ANOS: PRAZO_MIN_ANOS, PRAZO_MAX_ANOS: PRAZO_MAX_ANOS, IMOVEL_MIN: IMOVEL_MIN, IMOVEL_MAX: IMOVEL_MAX, RECEBER_MIN: RECEBER_MIN,
              ref: REF, ipcaMensal: ipcaMensal, taxaMensal: taxaMensal, pmt: pmt, valorPresente: valorPresente, limiteCredito: limiteCredito,
              simular: simular, receberParaParcela: receberParaParcela, amortizacaoAnual: amortizacaoAnual, compararQuitacao: compararQuitacao, brl: brl, pct: pct };
  root.DatalabHomeEquity = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
"""

NOT_FOUND = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Página não encontrada</title>
<meta name="robots" content="noindex">
<link rel="stylesheet" href="/styles.css">
</head>
<body>
<main class="wrap">
<section class="hero">
  <h1>Página não encontrada</h1>
  <p>O endereço não existe mais ou foi digitado errado.</p>
  <p class="fine"><a href="/">Voltar ao simulador de Home Equity</a></p>
</section>
</main>
</body>
</html>
"""

LLMS = """# Home Equity — simulador (Datalab Global)

> Simulador gratuito de Home Equity (crédito com imóvel em garantia): mostra a parcela e o custo total estimados antes de qualquer pedido. Libera até 60% do valor do imóvel, em até 20 anos, segundo o parceiro de crédito.

- Responsável: @@RAZAO@@, CNPJ @@CNPJ@@
- Atualizado em @@ATUALIZADO@@
- Conta: parcela fixa (tabela Price) sobre o crédito total; taxa de referência = 1,09% ao mês + IPCA em 12 meses (estimativa, não oferta). Detalhes em @@DOMINIO@@/metodologia
- Taxas de comparação: médias do Banco Central (SGS 29976, 20742, 20741, 22022 e IPCA 13522), em @@DOMINIO@@/taxas-de-referencia
- A simulação não é proposta de crédito; a taxa e o limite finais vêm da análise do parceiro.
- Dados das taxas (CSV): @@DOMINIO@@/dados/taxas-referencia.csv (séries do Banco Central, ODbL 1.0)
- Feed Atom: @@DOMINIO@@/feed.xml

## Páginas
@@LISTA@@
"""


def _preencher(texto, valores):
    for chave, valor in valores.items():
        texto = texto.replace("@@" + chave + "@@", valor)
    return texto


def referencias():
    """Referências do BCB para o simulador: IPCA em 12 meses e a média de crédito com garantia real (% a.m.). Falta dado -> levanta erro (não publicar sem taxa real)."""
    linhas = tr.ler()
    ipca = tr.ultima(tr.CODIGO_IPCA, linhas)
    gar = tr.ultima(tr.CODIGO_GARANTIA_REAL, linhas)
    if not ipca or not gar:
        raise SystemExit("dados/taxas_referencia.csv sem IPCA ou sem a série 29976: rode python etl_taxas.py")
    ref = {"ipca12m": ipca["valor"], "ipcaMes": conteudo.mes_curto(ipca["mes"]), "garantiaRealAm": tr.ao_mes(gar),
           "garantiaRealMes": conteudo.mes_curto(gar["mes"])}
    # Médias de mercado das dívidas caras (% a.m.), para o cenário "quitar dívida": chave no JS = chave aqui.
    for chave, codigo in (("pessoal", 20742), ("cheque", 20741), ("rotativo", 22022)):
        u = tr.ultima(codigo, linhas)
        if not u:
            raise SystemExit("dados/taxas_referencia.csv sem a série %d: rode python etl_taxas.py" % codigo)
        ref[chave + "Am"] = tr.ao_mes(u)
        ref[chave + "Mes"] = conteudo.mes_curto(u["mes"])
    return ref


def gerar_calculo_js():
    refs = json.dumps(referencias(), ensure_ascii=False, sort_keys=True)
    return _preencher(CALCULO_JS, {
        "TAXA_PARCEIRO": repr(calculo.TAXA_PARCEIRO_AM), "LTV": repr(calculo.LTV_MAX), "CREDITO_MAX": str(calculo.CREDITO_MAX), "PRAZO_MIN": str(calculo.PRAZO_MIN_ANOS), "PRAZO_MAX": str(calculo.PRAZO_MAX_ANOS),
        "IMOVEL_MIN": str(calculo.IMOVEL_MIN), "IMOVEL_MAX": str(calculo.IMOVEL_MAX), "RECEBER_MIN": str(calculo.RECEBER_MIN), "REFERENCIAS": refs})


def _resumo(dados):
    return hashlib.sha256(dados).hexdigest()[:10]


def _ler_bytes(*partes):
    with open(os.path.join(AQUI, *partes), "rb") as f:
        return f.read()


def versao_arquivo(*partes):
    return _resumo(_ler_bytes(*partes))


def home_scripts():
    """Os scripts também têm a versão no endereço: o Cloudflare guarda .js na borda por horas e ignora o max-age do _headers; com ?v=<resumo>
    o endereço muda junto com o conteúdo e ninguém recebe HTML novo com JS velho."""
    return ('<script src="/calculo.js?v=' + _resumo(gerar_calculo_js().encode("utf-8")) + '"></script>\n'
            '<script src="/simulador.js?v=' + versao_arquivo("src", "simulador.js") + '"></script>\n' + menu_script())


def menu_script():
    return '<script defer src="/menu.js?v=' + versao_arquivo("src", "menu.js") + '"></script>\n'


def versao_css():
    return versao_arquivo("src", "estilo.css")


def versao_icones():
    h = hashlib.sha256()
    for nome in ("favicon.ico", "favicon-32.png", "apple-touch-icon.png"):
        h.update(_ler_bytes("paginas_seo", nome))
    return h.hexdigest()[:10]


def versao_og_image():
    return _resumo(_ler_bytes("paginas_seo", "og-image.png"))


def _sem_tags(html):
    return re.sub(r"<[^>]+>", "", html).replace("&quot;", '"')


def _ld(dados):
    return '<script type="application/ld+json">' + json.dumps(dados, ensure_ascii=False) + "</script>\n"


def _umami():
    if not UMAMI_ID:
        return ""
    return '<script defer src="https://cloud.umami.is/script.js" data-website-id="' + UMAMI_ID + '"></script>\n'


# Navegação: poucos links no cabeçalho, tudo no menu do celular e no rodapé (em colunas).
DESTAQUES = ["como-funciona", "garantia-do-imovel", "taxas-de-referencia"]
ENTENDA = ["como-funciona", "garantia-do-imovel", "custos-alem-dos-juros", "home-equity-ou-outro-credito", "quando-nao-vale-a-pena"]
TRANSPARENCIA = ["taxas-de-referencia", "metodologia", "atualizacoes", "sobre"]
LEGAL = ["privacidade", "termos"]
ROTULOS = {"atualizacoes": "Atualizações", "privacidade": "Privacidade", "termos": "Termos de uso",
           "home-equity-ou-outro-credito": "Comparar com outros créditos", "taxas-de-referencia": "Taxas do Banco Central",
           "custos-alem-dos-juros": "Custos além dos juros", "garantia-do-imovel": "Garantia do imóvel",
           "quando-nao-vale-a-pena": "Quando não vale a pena", "como-funciona": "Como funciona"}


def _pg(slug):
    return next(pg for pg in conteudo.PAGINAS if pg["slug"] == slug)


def _rotulo(slug):
    return ROTULOS.get(slug) or _pg(slug).get("menu") or _pg(slug)["h1"]


def _nav_desktop():
    return '<a href="/#simulador">Simular</a>' + "".join('<a href="/' + s + '">' + _rotulo(s) + "</a>" for s in DESTAQUES)


def _nav_celular():
    links = ENTENDA + [s for s in TRANSPARENCIA if s not in ENTENDA]
    return '<a href="/#simulador">Simular</a>' + "".join('<a href="/' + s + '">' + _rotulo(s) + "</a>" for s in links)


def _lista_rodape(slugs, extra=""):
    return "".join('<li><a href="/' + s + '">' + _rotulo(s) + "</a></li>" for s in slugs) + extra


# Os outros simuladores da Datalab Global (outros produtos, outros subdomínios). O texto do link descreve o destino.
OUTROS_SIMULADORES = [
    ("https://emprestimo.datalabglobal.com/", "Pix no cartão de crédito"),
    ("https://simulador.datalabglobal.com/", "Financiamento imobiliário"),
    ("https://veiculos.datalabglobal.com/", "Financiamento de veículos"),
    (HUB + "/", "Datalab Global"),
]


def _lista_outros():
    return "".join('<li><a href="' + url + '">' + texto + "</a></li>" for url, texto in OUTROS_SIMULADORES)


def _faq_html():
    return "".join("<details><summary>" + q + "</summary><p>" + r + "</p></details>" for q, r in conteudo.FAQ)


def _cartoes_html():
    saida = ""
    for pg in conteudo.PAGINAS:
        if not pg.get("cartao"):
            continue
        saida += ('<a class="card" href="/' + pg["slug"] + '"><h4>' + pg["cartao"] + "</h4>" + pg["desc"] + '<span class="go">Ler →</span></a>')
    return saida


def _ctx(hoje):
    return {"razao": RAZAO_SOCIAL, "cnpj": CNPJ, "email": EMAIL, "atualizado": hoje.strftime("%d/%m/%Y"), "atualizacoes": conteudo.ATUALIZACOES}


def _organizacao():
    return {"@type": "Organization", "@id": DOMINIO + "/#organizacao", "name": "Datalab Global", "legalName": RAZAO_SOCIAL,
            "taxID": CNPJ, "url": HUB + "/", "email": EMAIL}


def _valores_padrao():
    """Números da simulação inicial (a mesma que o JS desenha ao abrir a página), escritos no HTML para quem lê sem JavaScript e para os buscadores."""
    ref = referencias()
    i = calculo.taxa_mensal(ref["ipca12m"])
    r = calculo.simular(800_000, 250_000, 0, 180, i)
    conforto = 3000
    dif = r["parcela"] - conforto
    raio = ("Com a estimativa de " + conteudo.brl0(r["parcela"]) + ", este cenário fica " + conteudo.brl0(dif) +
            " acima do valor que você informou. Veja o que muda com a mesma taxa:")
    amort = calculo.amortizacao_anual(r["credito"], i, 180)
    taxa_div = ref[conteudo.DIVIDA_TIPO_PADRAO + "Am"]
    q = calculo.comparar_quitacao(conteudo.DIVIDA_PADRAO, taxa_div / 100, 180, i)
    opcoes = "".join('<input type="radio" name="tipodiv" id="div-%s" value="%s"%s><label for="div-%s">%s <small>média %s a.m.</small></label>'
                     % (k, k, " checked" if k == conteudo.DIVIDA_TIPO_PADRAO else "", k, nome, conteudo.pct(ref[k + "Am"])) for k, nome in conteudo.DIVIDAS)
    opcoes += '<input type="radio" name="tipodiv" id="div-outra" value="outra"><label for="div-outra">Outra <small>informo a taxa</small></label>'
    return {
        "D_AMORT_RESUMO": conteudo.amort_resumo(r, amort), "D_AMORT_LINHAS": conteudo.amort_linhas(amort), "D_AMORT_TOTAL": conteudo.amort_total(amort, r["credito"]),
        "D_AMORT_NOTA": conteudo.amort_nota(ref),
        "DIVIDA_OPCOES": opcoes, "D_Q_CARTOES": conteudo.quitar_cartoes(q, taxa_div, 15, i * 100), "D_Q_TEXTO": conteudo.quitar_texto(q, 15),
        "D_ROSCA_P": "%.1f" % (r["credito"] / r["total"] * 289.0265), "D_PCT_JUROS": str(round(r["juros"] / r["total"] * 100)),
        "D_AMORT_PCT": str(round(amort[0]["juros"] / (r["parcela"] * 12) * 100)),
        "FATO_TAXA": conteudo.pct(calculo.TAXA_PARCEIRO_AM), "FATO_LTV": "%d%%" % round(calculo.LTV_MAX * 100), "FATO_PRAZO": "%d anos" % calculo.PRAZO_MAX_ANOS,
        "PRAZO_MIN": str(calculo.PRAZO_MIN_ANOS), "PRAZO_MAX": str(calculo.PRAZO_MAX_ANOS),
        "D_L_CRED": conteudo.brl0(r["credito"]), "D_L_JUROS": conteudo.brl0(r["juros"]),
        "D_PARCELA": conteudo.brl0(r["parcela"]), "D_TOTAL": conteudo.brl0(r["total"]),
        "D_SUB": "em 180 meses · taxa de referência " + conteudo.pct(i * 100) + " a.m.",
        "D_CREDITO": conteudo.brl0(r["credito"]) + " · " + str(round(r["ltv"] * 100)) + "%", "D_BARRA": "%.1f" % (r["ltv"] * 100),
        "D_LIMITE": conteudo.brl0(r["limite"]), "D_RAIO": raio,
        "NOTA_TAXA": conteudo.nota_taxa_maior(ref, i, 800_000, 250_000, 0, 180),
    }


def _comparacao_html():
    linhas = tr.ler()
    itens = []
    for codigo in tr.CODIGOS_COMPARACAO:
        u = tr.ultima(codigo, linhas)
        if u:
            itens.append((tr.serie_def(codigo)["nome"], tr.ao_mes(u), u["mes"], codigo))
    maximo = max(v for _, v, _, _ in itens)
    saida = '<div class="cmp">'
    for nome, v, _, codigo in itens:
        us = " us" if codigo == tr.CODIGO_GARANTIA_REAL else ""
        cor = "#4aa3b5" if us else "#475569"
        saida += ('<div class="r' + us + '"><span>' + nome + '</span><svg width="100%" height="12" role="img" aria-label="' + nome + ": " + conteudo.pct(v) +
                  ' ao mês"><rect width="100%%" height="12" rx="6" fill="rgba(255,255,255,.07)"/><rect width="%.1f%%" height="12" rx="6" fill="%s"/></svg><span class="vv num">' % (v / maximo * 100, cor)
                  + conteudo.pct(v) + " a.m.</span></div>")
    saida += "</div>"
    meses = sorted({m for _, _, m, _ in itens})
    saida += ('<div class="hint">Médias do mercado em ' + " e ".join(conteudo.mes_curto(m) for m in meses) + ' (Banco Central, séries SGS 29976, 20742, 20741 e 22022). '
              'É referência, não a taxa que você vai receber. <a href="/taxas-de-referencia">Veja as fontes</a>.</div>')
    return saida


def _pagina_home(valores, hoje):
    faq = {"@context": "https://schema.org", "@type": "FAQPage",
           "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": _sem_tags(r)}} for q, r in conteudo.FAQ]}
    site = {"@context": "https://schema.org", "@graph": [
        _organizacao(),
        {"@type": "WebSite", "@id": DOMINIO + "/#site", "url": DOMINIO + "/", "name": "Home Equity — Datalab Global", "inLanguage": "pt-BR",
         "publisher": {"@id": DOMINIO + "/#organizacao"}},
    ]}
    main = _preencher(layout.HOME_MAIN, dict(valores, COMPARACAO=_comparacao_html(), CARTOES=_cartoes_html(), FAQ=_faq_html(),
                                             PARCEIRO=LINK_PARCEIRO, **_valores_padrao()))
    return _preencher(layout.LAYOUT, dict(valores, TITLE=HOME_TITLE, DESC=HOME_DESC, CANONICAL=DOMINIO + "/", ROBOTS="index,follow,max-image-preview:large",
                                          OGTYPE="website", JSONLD=_ld(site) + _ld(faq), MAIN=main, SCRIPTS=home_scripts()))


def _pagina_guia(pg, valores, hoje, ctx):
    canonical = DOMINIO + "/" + pg["slug"]
    corpo = pg["corpo"](ctx)
    guia = pg.get("guia", True)
    cabecalho = _preencher(layout.GUIA_CABECALHO, dict(valores, ROTULO_PAGINA=pg.get("menu") or _rotulo(pg["slug"]), H1=pg["h1"]))
    if guia:
        outros = [x for x in conteudo.PAGINAS if x.get("cartao") and x["slug"] != pg["slug"]]
        i = next((k for k, x in enumerate(outros) if conteudo.PAGINAS.index(x) > conteudo.PAGINAS.index(pg)), 0)
        rel = "".join('<li><a href="/' + x["slug"] + '">' + x["h1"] + "</a></li>" for x in (outros[i:] + outros[:i])[:3])
        fecho = _preencher(layout.GUIA_FECHO, {"RELACIONADOS": rel})
    else:
        fecho = ""
    main = cabecalho + corpo + layout.GUIA_MEIO + fecho + "</article>"
    artigo = {"@context": "https://schema.org", "@type": "Article", "headline": pg["h1"], "description": pg["desc"], "inLanguage": "pt-BR",
              "dateModified": hoje.isoformat(), "mainEntityOfPage": canonical,
              "author": {"@type": "Organization", "name": "Datalab Global"}, "publisher": _organizacao()}
    return _preencher(layout.LAYOUT, dict(valores, TITLE=pg["title"], DESC=pg["desc"], CANONICAL=canonical, ROBOTS="index,follow,max-image-preview:large",
                                          OGTYPE="article" if guia else "website", JSONLD=_ld(artigo) if guia else "", MAIN=main, SCRIPTS=menu_script()))


def _ler_manifesto(caminho):
    if not caminho:
        return {}
    try:
        with open(caminho, encoding="utf-8") as f:
            dados = json.load(f)
    except (OSError, ValueError):
        return {}
    return dados if isinstance(dados, dict) else {}


def _gravar_manifesto(caminho, dados):
    texto = json.dumps(dados, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    try:
        with open(caminho, encoding="utf-8", newline="") as f:
            if f.read() == texto:
                return
    except OSError:
        pass
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)


def _impressao(html):
    """Resumo do conteúdo da página sem o que muda sem mudar o texto: a data (a página é gerada com uma data fixa) e as versões (?v=) dos arquivos."""
    return _resumo(re.sub(r"\?v=[0-9a-f]+", "?v=X", html).encode("utf-8"))


def _datas_das_paginas(feitas, hoje, manifesto):
    """feitas: {chave: função(data) -> html}. Devolve ({chave: data}, manifesto novo).

    A data de uma página só vai para hoje quando o conteúdo dela mudou desde a última geração; se não mudou, fica a data guardada.
    Assim o "Atualizado em", o lastmod do sitemap e o dateModified não mentem quando o robô semanal só regera o site."""
    datas, novo = {}, {}
    for chave, fazer in feitas.items():
        h = _impressao(fazer(DATA_SENTINELA))
        antigo = manifesto.get(chave) or {}
        data = hoje
        if antigo.get("hash") == h:
            try:
                data = datetime.date.fromisoformat(antigo.get("data", ""))
            except ValueError:
                data = hoje
        datas[chave] = data
        novo[chave] = {"hash": h, "data": data.isoformat()}
    return datas, novo


def gerar_site(saida=SAIDA_PADRAO, hoje=None, manifesto=None):
    """manifesto: arquivo com as datas das páginas. Sem ele (e fora da pasta padrão, como nos testes) todas as páginas levam a data de hoje."""
    hoje = hoje or datetime.date.today()
    if manifesto is None and os.path.abspath(saida) == os.path.abspath(SAIDA_PADRAO):
        manifesto = MANIFESTO_PADRAO
    os.makedirs(saida, exist_ok=True)
    for sub in ("fonts", "dados"):
        os.makedirs(os.path.join(saida, sub), exist_ok=True)
    if os.path.abspath(saida) != os.path.abspath(SAIDA_PADRAO):
        for nome in os.listdir(os.path.join(SAIDA_PADRAO, "fonts")):
            shutil.copyfile(os.path.join(SAIDA_PADRAO, "fonts", nome), os.path.join(saida, "fonts", nome))
        for nome in ("favicon.ico", "favicon-32.png", "favicon-192.png", "apple-touch-icon.png", "og-image.png"):
            shutil.copyfile(os.path.join(SAIDA_PADRAO, nome), os.path.join(saida, nome))
    shutil.copyfile(os.path.join(AQUI, "src", "estilo.css"), os.path.join(saida, "styles.css"))
    valores = {
        "DOMINIO": DOMINIO, "HUB": HUB, "UMAMI": _umami(), "RAZAO": RAZAO_SOCIAL, "CNPJ": CNPJ, "EMAIL": EMAIL, "LOGO": layout.LOGO,
        "CSSV": versao_css(), "ICONV": versao_icones(), "OGV": versao_og_image(), "NAV": _nav_desktop(), "NAVMOBILE": _nav_celular(),
        "FOOT_ENTENDA": _lista_rodape(ENTENDA), "FOOT_LEGAL": _lista_rodape(LEGAL), "FOOT_OUTROS": _lista_outros(),
        "FOOT_TRANSP": _lista_rodape(TRANSPARENCIA, '<li><a href="/feed.xml">Feed Atom</a></li><li><a href="/dados/taxas-referencia.csv">Dados das taxas (CSV)</a></li>'),
    }

    def escrever(nome, texto):
        with open(os.path.join(saida, nome), "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)

    def com_data(d):
        return dict(valores, ATUALIZADO=d.strftime("%d/%m/%Y"))

    feitas = {"index": lambda d: _pagina_home(com_data(d), d)}
    for pg in conteudo.PAGINAS:
        feitas[pg["slug"]] = (lambda pg_: lambda d: _pagina_guia(pg_, com_data(d), d, _ctx(d)))(pg)
    datas, novo_manifesto = _datas_das_paginas(feitas, hoje, _ler_manifesto(manifesto))
    escrever("index.html", feitas["index"](datas["index"]))
    for pg in conteudo.PAGINAS:
        escrever(pg["slug"] + ".html", feitas[pg["slug"]](datas[pg["slug"]]))
    if manifesto:
        _gravar_manifesto(manifesto, novo_manifesto)
    valores["ATUALIZADO"] = max(datas.values()).strftime("%d/%m/%Y")  # llms.txt: a data da página mais recente
    escrever("404.html", NOT_FOUND.replace("/styles.css", "/styles.css?v=" + valores["CSSV"]))
    escrever(indexnow.CHAVE + ".txt", indexnow.CHAVE + "\n")
    escrever("feed.xml", feed_atom.gerar(hoje))
    shutil.copyfile(tr.CAMINHO_CSV, os.path.join(saida, "dados", "taxas-referencia.csv"))
    escrever("calculo.js", gerar_calculo_js())
    shutil.copyfile(os.path.join(AQUI, "src", "simulador.js"), os.path.join(saida, "simulador.js"))
    shutil.copyfile(os.path.join(AQUI, "src", "menu.js"), os.path.join(saida, "menu.js"))
    os.makedirs(os.path.join(saida, ".well-known"), exist_ok=True)
    escrever(".well-known/security.txt", "Contact: mailto:" + EMAIL + "\nExpires: " + (hoje + datetime.timedelta(days=365)).isoformat() +
             "T00:00:00.000Z\nPreferred-Languages: pt, en\nCanonical: " + DOMINIO + "/.well-known/security.txt\n")
    escrever("_headers", _preencher(HEADERS, {"CSP": CSP}))
    escrever("robots.txt", "User-agent: *\nAllow: /\n\nSitemap: " + DOMINIO + "/sitemap.xml\n")
    linhas = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for caminho in PAGINAS_INDEXAVEIS:
        linhas.append("  <url><loc>" + DOMINIO + caminho + "</loc><lastmod>" + datas["index" if caminho == "/" else caminho[1:]].isoformat() + "</lastmod></url>")
    linhas.append("</urlset>")
    escrever("sitemap.xml", "\n".join(linhas) + "\n")
    lista = "\n".join("- " + DOMINIO + c for c in PAGINAS_INDEXAVEIS)
    escrever("llms.txt", _preencher(LLMS, dict(valores, LISTA=lista)))
    return saida


if __name__ == "__main__":
    pasta = sys.argv[1] if len(sys.argv) > 1 else SAIDA_PADRAO
    print("Site gerado em", gerar_site(pasta))
