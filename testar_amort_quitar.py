"""Teste de navegador (Chromium e WebKit, computador e celular) da amortização ano a ano e do "quitar dívida cara".

Sobe paginas_seo/ localmente, bloqueia o Umami e confere cada número contra calculo.py. Uso: python testar_amort_quitar.py (precisa do Playwright; fora do CI).
"""
import functools
import http.server
import os
import re
import sys
import threading

from playwright.sync_api import sync_playwright

import calculo
import gerador_homeequity as g

AQUI = os.path.dirname(os.path.abspath(__file__))
PORTA = 8812
FALHAS = []
REF = g.referencias()
I = calculo.taxa_mensal(REF["ipca12m"])


def confere(nome, cond, detalhe=""):
    print(("OK    " if cond else "FALHOU") + " " + nome + (" -> " + str(detalhe) if not cond or detalhe else ""))
    if not cond:
        FALHAS.append(nome)


def n(texto):
    return int(re.sub(r"[^\d]", "", texto))


def linhas_tabela(pg):
    return pg.eval_on_selector_all("#amort-corpo tr", "trs => trs.map(t => [...t.children].map(c => c.textContent))")


def rodar(nav, nome_nav, base, largura):
    tag = nome_nav + "/" + str(largura)
    ctx = nav.new_context(viewport={"width": largura, "height": 900})
    pg = ctx.new_page()
    erros = []
    pg.on("console", lambda m: erros.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: erros.append("PAGEERROR " + str(e)))
    pg.route("**/*umami*", lambda r: r.abort())
    eventos = []
    pg.add_init_script("window.umami={track:function(n,d){window.__ev=(window.__ev||[]);window.__ev.push([n,d||null]);}};")
    pg.goto(base + "/")
    pg.wait_for_selector("#alts .alt")

    # --- amortização
    ab = pg.evaluate("document.getElementById('det-amort').open")
    confere(tag + ": amortização começa recolhida", ab is False)
    pg.click("#det-amort summary")
    confere(tag + ": abre ao clicar", pg.evaluate("document.getElementById('det-amort').open") is True)
    r = calculo.simular(800_000, 250_000, 0, 180, I)
    esp = calculo.amortizacao_anual(r["credito"], I, 180)
    lin = linhas_tabela(pg)
    confere(tag + ": 15 linhas de ano", len(lin) == 15, len(lin))
    ok = all(n(l[1]) == round(e["juros"]) and n(l[2]) == round(e["amortizacao"]) and n(l[3]) == round(e["saldo"]) for l, e in zip(lin, esp))
    confere(tag + ": tabela igual ao calculo.py", ok, lin[0])
    confere(tag + ": saldo final zero", n(lin[-1][3]) == 0)
    # muda prazo e valor: a tabela acompanha
    pg.select_option("#sel-prazo", "8")
    pg.fill("#campo-receber", "180.000")
    pg.press("#campo-receber", "Enter")
    pg.wait_for_timeout(300)
    r2 = calculo.simular(800_000, 180_000, 0, 96, I)
    esp2 = calculo.amortizacao_anual(r2["credito"], I, 96)
    lin2 = linhas_tabela(pg)
    confere(tag + ": tabela acompanha prazo e valor", len(lin2) == 8 and all(n(l[1]) == round(e["juros"]) and n(l[3]) == round(e["saldo"]) for l, e in zip(lin2, esp2)), len(lin2))
    resumo = pg.inner_text("#amort-resumo")
    pago = r2["parcela"] * 12
    confere(tag + ": resumo cita juros do 1º ano", ("%d%%" % round(esp2[0]["juros"] / pago * 100)) in resumo, resumo)
    rodape = pg.inner_text("#amort-rodape")
    confere(tag + ": total de juros no rodapé", n(rodape.split("\t")[1]) == round(sum(e["juros"] for e in esp2)), rodape)

    # --- quitar dívida
    pg.goto(base + "/")
    pg.wait_for_selector("#q-cartoes .alt")
    cartoes = pg.inner_text("#q-cartoes")
    q = calculo.comparar_quitacao(60_000, REF["pessoalAm"] / 100, 180, I)
    confere(tag + ": padrão mostra a parcela na taxa média e no Home Equity", str(round(q["parcela_atual"])) in re.sub(r"[^\d\n]", "", cartoes.replace(".", "")) and
            str(round(q["parcela_he"])) in cartoes.replace(".", ""), cartoes[:120])
    for tipo, chave in (("cheque", "chequeAm"), ("rotativo", "rotativoAm"), ("pessoal", "pessoalAm")):
        pg.select_option("#sel-divida", tipo)
        pg.wait_for_timeout(150)
        qq = calculo.comparar_quitacao(60_000, REF[chave] / 100, 180, I)
        txt = pg.inner_text("#q-cartoes").replace(".", "")
        confere(tag + ": tipo " + tipo, str(round(qq["parcela_atual"])) in txt and str(round(qq["parcela_he"])) in txt, txt[:90])
    # valor da dívida
    pg.fill("#campo-divida", "120.000")
    pg.press("#campo-divida", "Enter")
    pg.wait_for_timeout(200)
    q3 = calculo.comparar_quitacao(120_000, REF["pessoalAm"] / 100, 180, I)
    txt = pg.inner_text("#q-cartoes").replace(".", "")
    confere(tag + ": valor da dívida", str(round(q3["parcela_atual"])) in txt and str(round(q3["parcela_he"])) in txt)
    # taxa própria
    pg.select_option("#sel-divida", "outra")
    confere(tag + ": campo de taxa aparece", pg.is_visible("#campo-taxa-div"))
    pg.fill("#campo-taxa-div", "3,5")
    pg.press("#campo-taxa-div", "Enter")
    pg.wait_for_timeout(200)
    q4 = calculo.comparar_quitacao(120_000, 0.035, 180, I)
    txt = pg.inner_text("#q-cartoes").replace(".", "")
    confere(tag + ": taxa própria", str(round(q4["parcela_atual"])) in txt and "Na taxa da sua dívida (3,50% a.m.)" in pg.inner_text("#q-cartoes"), txt[:90])
    # taxa menor que a do Home Equity: sem economia
    pg.fill("#campo-taxa-div", "1")
    pg.press("#campo-taxa-div", "Enter")
    pg.wait_for_timeout(200)
    confere(tag + ": taxa baixa não promete economia", "não reduz a parcela" in pg.inner_text("#q-texto"), pg.inner_text("#q-texto"))
    # taxa inválida
    pg.fill("#campo-taxa-div", "99")
    pg.press("#campo-taxa-div", "Enter")
    pg.wait_for_timeout(200)
    confere(tag + ": taxa absurda avisa e esconde o resultado", pg.is_visible("#q-aviso") and pg.locator("#q-cartoes .alt").count() == 0 and pg.is_disabled("#btn-usar-divida"))
    pg.fill("#campo-taxa-div", "")
    pg.press("#campo-taxa-div", "Enter")
    pg.fill("#campo-taxa-div", "6")
    pg.press("#campo-taxa-div", "Enter")
    # dívida abaixo do mínimo e acima do limite
    pg.fill("#campo-divida", "20.000")
    pg.press("#campo-divida", "Enter")
    pg.wait_for_timeout(200)
    confere(tag + ": dívida pequena avisa do mínimo de mercado", "mínimo" in pg.inner_text("#q-aviso") and pg.is_visible("#q-aviso"))
    pg.fill("#campo-divida", "2.000.000")
    pg.press("#campo-divida", "Enter")
    pg.wait_for_timeout(200)
    confere(tag + ": dívida acima do limite usa o limite", "limite do imóvel cobre até" in pg.inner_text("#q-aviso"), pg.inner_text("#q-aviso"))
    pg.fill("#campo-divida", "")
    pg.press("#campo-divida", "Enter")
    pg.wait_for_timeout(200)
    confere(tag + ": dívida vazia pede o valor", "Informe quanto" in pg.inner_text("#q-aviso"))
    # botão "simular com este valor"
    pg.fill("#campo-divida", "90.000")
    pg.press("#campo-divida", "Enter")
    pg.click("#btn-usar-divida")
    pg.wait_for_timeout(300)
    confere(tag + ": 'Simular com este valor' leva a dívida ao campo de receber", n(pg.input_value("#campo-receber")) == 90_000, pg.input_value("#campo-receber"))
    pg.fill("#campo-divida", "20.000")
    pg.press("#campo-divida", "Enter")
    pg.click("#btn-usar-divida")
    pg.wait_for_timeout(300)
    confere(tag + ": abaixo do mínimo vira o mínimo e avisa certo", n(pg.input_value("#campo-receber")) == calculo.RECEBER_MIN and "mínimo" in pg.inner_text("#msg-ajuste"),
            pg.inner_text("#msg-ajuste"))
    # medição
    ev = pg.evaluate("window.__ev || []")
    nomes = [e[0] for e in ev]
    confere(tag + ": eventos novos uma vez cada", nomes.count("usou-quitar-divida") == 1 and nomes.count("abriu-amortizacao") == 0, nomes)
    confere(tag + ": sem dado pessoal nos eventos", all(set((e[1] or {}).keys()) <= {"tipo", "prazo", "receber"} for e in ev), ev)
    # sem rolagem lateral e sem erro
    ow = pg.evaluate("document.documentElement.scrollWidth - innerWidth")
    confere(tag + ": sem rolagem horizontal", ow <= 0, ow)
    confere(tag + ": sem erro no console", not [e for e in erros if "beacon" not in e.lower() and "cloudflareinsights" not in e.lower()], erros[:2])
    ctx.close()


def main():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=os.path.join(AQUI, "paginas_seo"))
    handler.log_message = lambda *a, **k: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORTA), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d" % PORTA
    with sync_playwright() as p:
        for nome, motor in (("chromium", p.chromium), ("webkit", p.webkit)):
            nav = motor.launch()
            for largura in (1280, 390):
                rodar(nav, nome, base, largura)
            nav.close()
    srv.shutdown()
    print("\n%d falha(s)" % len(FALHAS))
    sys.exit(1 if FALHAS else 0)


if __name__ == "__main__":
    main()
