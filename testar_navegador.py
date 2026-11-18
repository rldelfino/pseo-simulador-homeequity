"""Teste de ponta a ponta no navegador (Chromium e WebKit): abre o site gerado e usa o simulador como uma pessoa usaria.

Precisa do Playwright (fora do CI). Sobe um servidor local em paginas_seo/, bloqueia o Umami (não contaminar a medição) e confere os números
contra calculo.py. Uso: python testar_navegador.py
"""
import functools
import http.server
import os
import re
import sys
import threading

from playwright.sync_api import sync_playwright

import calculo
import conteudo

AQUI = os.path.dirname(os.path.abspath(__file__))
PORTA = 8811
FALHAS = []


def confere(nome, cond, detalhe=""):
    print(("OK    " if cond else "FALHOU") + " " + nome + (" -> " + str(detalhe) if not cond or detalhe else ""))
    if not cond:
        FALHAS.append(nome)


def numero(texto):
    return int(re.sub(r"[^\d]", "", texto))


def esperado(imovel, receber, saldo, anos):
    i = calculo.taxa_mensal(conteudo._ref()["ipca12m"])
    return calculo.simular(imovel, receber, saldo, anos * 12, i)


def rodar(nav, nome_nav, base, largura):
    ctx = nav.new_context(viewport={"width": largura, "height": 900})
    pg = ctx.new_page()
    erros = []
    pg.on("console", lambda m: erros.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: erros.append("PAGEERROR " + str(e)))
    pg.route("**/*umami*", lambda r: r.abort())
    eventos = []
    pg.add_init_script("window.umami={track:function(n,d){window.__ev=(window.__ev||[]);window.__ev.push([n,d]);}}")
    tag = nome_nav + "/" + str(largura) + ": "

    pg.goto(base + "/")
    pg.wait_for_selector("#alts .alt")
    r = esperado(800_000, 250_000, 0, 15)
    confere(tag + "parcela inicial", numero(pg.inner_text("#r-parcela")) == round(r["parcela"]), pg.inner_text("#r-parcela"))
    confere(tag + "total inicial", numero(pg.inner_text("#r-total")) == round(r["total"]), pg.inner_text("#r-total"))
    confere(tag + "três cartões no Raio-X", pg.locator("#alts .alt").count() == 3)

    # prazo
    pg.select_option("#sel-prazo", "20")
    r = esperado(800_000, 250_000, 0, 20)
    confere(tag + "prazo 20 anos", numero(pg.inner_text("#r-parcela")) == round(r["parcela"]), pg.inner_text("#r-parcela"))
    confere(tag + "texto do prazo", "240 meses" in pg.inner_text("#r-sub"))
    pg.select_option("#sel-prazo", "15")

    # valor do imóvel e a receber (digitando)
    pg.fill("#campo-imovel", "1.000.000")
    pg.fill("#campo-receber", "400.000")
    pg.press("#campo-receber", "Enter")
    r = esperado(1_000_000, 400_000, 0, 15)
    confere(tag + "imóvel 1 milhão e receber 400 mil", numero(pg.inner_text("#r-parcela")) == round(r["parcela"]), pg.inner_text("#r-parcela"))
    confere(tag + "barra do limite", numero(pg.inner_text("#c-limite")) == 600_000, pg.inner_text("#c-limite"))

    # acima do limite: é ajustado e avisa
    pg.fill("#campo-receber", "900.000")
    pg.press("#campo-receber", "Enter")
    confere(tag + "ajusta ao limite de 60%", numero(pg.input_value("#campo-receber")) == 600_000, pg.input_value("#campo-receber"))
    confere(tag + "avisa do ajuste", pg.is_visible("#msg-ajuste") and "limite" in pg.inner_text("#msg-ajuste"), pg.inner_text("#msg-ajuste"))

    # imóvel financiado
    pg.fill("#campo-imovel", "800.000")
    pg.press("#campo-imovel", "Enter")
    pg.fill("#campo-receber", "250.000")
    pg.press("#campo-receber", "Enter")
    pg.click("label[for=sit-financiado]")
    confere(tag + "mostra o saldo devedor", pg.is_visible("#campo-saldo"))
    pg.fill("#campo-saldo", "200.000")
    pg.press("#campo-saldo", "Enter")
    r = esperado(800_000, 250_000, 200_000, 15)
    confere(tag + "saldo entra no crédito", numero(pg.inner_text("#r-parcela")) == round(r["parcela"]), pg.inner_text("#r-parcela"))
    confere(tag + "crédito + % do imóvel", numero(pg.inner_text("#c-credito").split("·")[0]) == 450_000, pg.inner_text("#c-credito"))
    pg.fill("#campo-saldo", "480.000")
    pg.press("#campo-saldo", "Enter")
    confere(tag + "sem margem: avisa e trava o botão", pg.is_disabled("#btn-cta") and pg.inner_text("#r-parcela") == "—", pg.inner_text("#msg-ajuste"))
    pg.click("label[for=sit-quitado]")
    confere(tag + "voltar a quitado zera o saldo", numero(pg.input_value("#campo-saldo")) == 0 and not pg.is_disabled("#btn-cta"))

    # Raio-X
    pg.fill("#campo-conforto", "3.000")
    pg.press("#campo-conforto", "Enter")
    r = esperado(800_000, 250_000, 0, 15)
    confere(tag + "raio-x diz quanto fica acima", conteudo.brl0(r["parcela"] - 3000) in pg.inner_text("#raio-texto").replace(chr(160), " "), pg.inner_text("#raio-texto"))
    confere(tag + "receber menos cabe na parcela", "cabe na parcela" in pg.inner_text("#alts"), pg.inner_text("#alts"))
    pg.fill("#campo-conforto", "9.000")
    pg.press("#campo-conforto", "Enter")
    confere(tag + "raio-x quando cabe", "abaixo" in pg.inner_text("#raio-texto").replace(chr(160), " "), pg.inner_text("#raio-texto"))

    # nota "e se a taxa for maior?"
    confere(tag + "nota da taxa maior", "2,14%" in pg.inner_text("#nota-taxa-texto"), pg.inner_text("#nota-taxa-texto"))

    # confirmação e link do parceiro
    pg.click("#btn-cta")
    confere(tag + "abre a tela de confirmação", pg.is_visible("#dlg-confirma"))
    href = pg.get_attribute("#a-parceiro", "href")
    confere(tag + "botão leva ao link do parceiro", href.startswith("https://proposta.api.br/f/"), href)
    pg.click("#btn-voltar")
    confere(tag + "voltar fecha a tela", not pg.is_visible("#dlg-confirma"))

    # endereço compartilhável
    url = pg.evaluate("window.location.href")
    pg.wait_for_timeout(600)
    url = pg.evaluate("window.location.href")
    confere(tag + "endereço guarda a simulação", "receber=250000" in url and "prazo=15" in url and "imovel=800000" in url, url)
    pg2 = ctx.new_page()
    pg2.route("**/*umami*", lambda r_: r_.abort())
    pg2.goto(base + "/?imovel=1500000&receber=300000&prazo=10&saldo=100000&conforto=4000#simulador")
    pg2.wait_for_selector("#alts .alt")
    r = esperado(1_500_000, 300_000, 100_000, 10)
    confere(tag + "abre pelo link compartilhado", numero(pg2.inner_text("#r-parcela")) == round(r["parcela"]), pg2.inner_text("#r-parcela"))
    confere(tag + "link: situação financiado", pg2.is_checked("#sit-financiado"))
    pg2.goto(base + "/?imovel=abc&receber=-5&prazo=99")
    pg2.wait_for_selector("#alts .alt")
    confere(tag + "endereço inválido cai no padrão", numero(pg2.inner_text("#r-parcela")) == round(esperado(800_000, 250_000, 0, 15)["parcela"]))
    pg2.close()

    # eventos de medição
    ev = pg.evaluate("window.__ev || []")
    nomes = [e[0] for e in ev]
    confere(tag + "eventos de medição", "usou-simulador-homeequity" in nomes and "abriu-confirmacao" in nomes, nomes)
    confere(tag + "sem dado pessoal nos eventos", all(set((e[1] or {}).keys()) <= {"receber", "prazo"} for e in ev))

    # layout: sem rolagem horizontal
    larg = pg.evaluate("[document.documentElement.scrollWidth, window.innerWidth]")
    confere(tag + "sem rolagem horizontal", larg[0] <= larg[1], larg)

    # páginas de guia
    for slug in ("como-funciona", "garantia-do-imovel", "custos-alem-dos-juros", "home-equity-ou-outro-credito", "quando-nao-vale-a-pena",
                 "taxas-de-referencia", "metodologia", "sobre", "atualizacoes", "privacidade", "termos"):
        pg2 = ctx.new_page()
        pg2.route("**/*umami*", lambda r_: r_.abort())
        resp = pg2.goto(base + "/" + slug)
        larg = pg2.evaluate("[document.documentElement.scrollWidth, window.innerWidth]")
        confere(tag + "página /" + slug, resp.status == 200 and larg[0] <= larg[1] and pg2.locator("h1").count() == 1, (resp.status, larg))
        pg2.close()

    confere(tag + "sem erro no console", not erros, erros)
    pg.close()
    ctx.close()


def main():
    pasta = os.path.join(AQUI, "paginas_seo")
    class Servidor(http.server.SimpleHTTPRequestHandler):
        """Como o Cloudflare Pages: /pagina abre pagina.html."""
        def translate_path(self, path):
            p = super().translate_path(path)
            if not os.path.exists(p) and os.path.exists(p + ".html"):
                return p + ".html"
            return p

        def log_message(self, *a, **k):
            pass

    handler = functools.partial(Servidor, directory=pasta)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORTA), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d" % PORTA
    with sync_playwright() as pw:
        for nome in ("chromium", "webkit"):
            try:
                nav = getattr(pw, nome).launch()
            except Exception as e:  # navegador não instalado
                print("AVISO: " + nome + " indisponível (" + str(e)[:80] + ")")
                continue
            for largura in (1200, 390):
                rodar(nav, nome, base, largura)
            nav.close()
    srv.shutdown()
    print("\n%d falha(s)" % len(FALHAS))
    sys.exit(1 if FALHAS else 0)


if __name__ == "__main__":
    main()
