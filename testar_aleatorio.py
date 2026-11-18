"""Teste aleatório da interface (fora do CI): ações aleatórias e, a cada passo, confere a tela contra calculo.py. Uso: python testar_aleatorio.py"""
import functools, http.server, os, random, re, sys, threading
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import calculo, conteudo

AQUI = os.path.dirname(os.path.abspath(__file__))
PORTA = 8814
FALHAS = []
I = calculo.taxa_mensal(conteudo._ref()["ipca12m"])


def num(t):
    d = re.sub(r"[^\d]", "", t or "")
    return int(d) if d else None


class H(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, p):
        r = super().translate_path(p.split("?")[0])
        return r + ".html" if not os.path.exists(r) and os.path.exists(r + ".html") else r

    def log_message(self, *a):
        pass


def estado(pg):
    return pg.evaluate("""() => ({
      imovel: document.getElementById('campo-imovel').value, saldo: document.getElementById('campo-saldo').value,
      receber: document.getElementById('campo-receber').value, anos: document.getElementById('sel-prazo').value,
      fin: document.getElementById('sit-financiado').checked,
      parcela: document.getElementById('r-parcela').textContent, total: document.getElementById('r-total').textContent,
      credito: document.getElementById('c-credito').textContent, limite: document.getElementById('c-limite').textContent,
      rotLim: document.getElementById('c-limite-rot').textContent,
      barra: document.getElementById('bar-fill').getAttribute('width'), marca: document.getElementById('bar-mark').getAttribute('x'),
      btnOff: document.getElementById('btn-cta').disabled, aviso: document.getElementById('msg-ajuste').hidden ? '' : document.getElementById('msg-ajuste').textContent,
      alts: [...document.querySelectorAll('#alts .alt')].map(a => a.innerText), nota: document.getElementById('nota-taxa-texto').textContent,
      rmin: document.getElementById('range-receber').min, rmax: document.getElementById('range-receber').max,
      url: location.href, ctav: document.getElementById('c-imovel').textContent})""")


def confere(nome, cond, detalhe=""):
    if not cond:
        FALHAS.append((nome, detalhe))
        print("FALHOU", nome, detalhe)


def invariantes(pg, passo, acao):
    e = estado(pg)
    im, sa, rc, an = num(e["imovel"]), num(e["saldo"]) or 0, num(e["receber"]), int(e["anos"])
    t = "[%s] %s | " % (passo, acao)
    for k in ("parcela", "total", "credito", "limite", "ctav"):
        confere(t + "sem NaN em " + k, "NaN" not in e[k] and "Infinity" not in e[k] and "undefined" not in e[k], e[k])
    confere(t + "imóvel dentro da faixa", calculo.IMOVEL_MIN <= im <= calculo.IMOVEL_MAX, im)
    lim = calculo.limite_credito(im)
    confere(t + "limite exibido = conta", abs(num(e["limite"]) - round(lim)) <= 1, (e["limite"], lim))
    rot_esperado = "teto" if calculo.LTV_MAX * im > calculo.CREDITO_MAX else "60%"
    confere(t + "rótulo do limite", rot_esperado in e["rotLim"], e["rotLim"])
    # marca do limite na barra = limite/imóvel
    confere(t + "marca da barra", abs(float(e["marca"].rstrip("%")) - min(99, lim / im * 100)) < 0.2, (e["marca"], lim / im * 100))
    if e["parcela"] == "—":
        confere(t + "sem margem: botão travado", e["btnOff"])
        return e
    confere(t + "botão liberado", not e["btnOff"])
    confere(t + "a receber dentro do limite", rc + sa <= lim + 1, (rc, sa, lim))
    confere(t + "a receber >= mínimo ou limite", rc >= min(calculo.RECEBER_MIN, lim - sa) - 1, (rc, lim - sa))
    r = calculo.simular(im, rc, sa, an * 12, I)
    confere(t + "parcela", abs(num(e["parcela"]) - round(r["parcela"])) <= 1, (e["parcela"], r["parcela"]))
    confere(t + "total", abs(num(e["total"]) - round(r["total"])) <= 1, (e["total"], r["total"]))
    pct = int(re.search(r"(\d+)%", e["credito"]).group(1))
    confere(t + "percentual do crédito", pct == round(r["ltv"] * 100), (e["credito"], r["ltv"] * 100))
    confere(t + "barra de uso", abs(float(e["barra"].rstrip("%")) - min(100, r["ltv"] * 100)) < 0.2, (e["barra"], r["ltv"] * 100))
    confere(t + "crédito exibido", abs(num(e["credito"].split("·")[0]) - round(r["credito"])) <= 1, e["credito"])
    # cartões do Raio-X: três e coerentes
    confere(t + "2 ou 3 cartões", len(e["alts"]) in (2, 3), len(e["alts"]))
    if len(e["alts"]) in (2, 3):
        p1 = num(e["alts"][0].split("\n")[1])
        confere(t + "cartão 1 = parcela", abs(p1 - round(r["parcela"])) <= 1, (p1, r["parcela"]))
        m = re.search(r"Receber (?:menos|mais): R\$\s?([\d.]+)", e["alts"][1] if len(e["alts"]) > 1 else "")
        if m:
            v = int(m.group(1).replace(".", ""))
            r2 = calculo.simular(im, v, sa, an * 12, I)
            p2 = num(e["alts"][1].split("\n")[1])
            confere(t + "cartão 2 = conta", abs(p2 - round(r2["parcela"])) <= 1, (p2, r2["parcela"]))
            confere(t + "cartão 2 dentro do limite e do mínimo", calculo.RECEBER_MIN <= v and v + sa <= lim + 1, (v, lim))
        m3 = re.search(r"Prazo (?:maior|menor): (\d+) anos", e["alts"][-1])
        if m3:
            r3 = calculo.simular(im, rc, sa, int(m3.group(1)) * 12, I)
            p3 = num(e["alts"][-1].split("\n")[1])
            confere(t + "cartão 3 = conta", abs(p3 - round(r3["parcela"])) <= 1, (p3, r3["parcela"]))
    # nota da taxa maior
    mm = re.search(r"seria de R\$\s?([\d.]+)", e["nota"])
    if mm:
        rm = calculo.simular(im, rc, sa, an * 12, 0.0214)
        confere(t + "nota taxa maior", abs(int(mm.group(1).replace(".", "")) - round(rm["parcela"])) <= 1, (mm.group(1), rm["parcela"]))
    # o endereço compartilhável reabre igual (depois do atraso do replaceState)
    return e


def rodar(nav, nome, seed, passos):
    rnd = random.Random(seed)
    ctx = nav.new_context(viewport={"width": 1100, "height": 900})
    ctx.route("**/*umami*", lambda r: r.abort())
    pg = ctx.new_page()
    erros = []
    pg.on("pageerror", lambda x: erros.append(str(x)))
    pg.on("console", lambda m: erros.append(m.text) if m.type == "error" else None)
    pg.goto("http://127.0.0.1:%d/" % PORTA)
    pg.wait_for_selector("#alts .alt")
    histor = []
    for k in range(passos):
        a = rnd.choice(["imovel", "imovel", "receber", "receber", "saldo", "prazo", "fin", "quit", "slider_i", "slider_r", "conforto", "sujo"])
        if a == "imovel":
            v = rnd.choice([100000, 150000, 480000, 800000, 1234567, 3000000, 5555000, 20000000, 99999, rnd.randint(100000, 9000000)])
            pg.fill("#campo-imovel", f"{v:,}".replace(",", ".")); pg.press("#campo-imovel", "Enter"); d = "imovel=%d" % v
        elif a == "receber":
            v = rnd.choice([1, 49999, 50000, 100000, 250000, 480000, 900000, 3000000, 9999999, rnd.randint(50000, 3000000)])
            pg.fill("#campo-receber", f"{v:,}".replace(",", ".")); pg.press("#campo-receber", "Enter"); d = "receber=%d" % v
        elif a == "saldo":
            if not pg.is_checked("#sit-financiado"):
                pg.click("label[for=sit-financiado]")
            v = rnd.choice([0, 1000, 100000, 200000, 480000, 2000000, rnd.randint(0, 900000)])
            pg.fill("#campo-saldo", f"{v:,}".replace(",", ".")); pg.press("#campo-saldo", "Enter"); d = "saldo=%d" % v
        elif a == "prazo":
            v = rnd.choice([5, 8, 10, 12, 15, 18, 20]); pg.select_option("#sel-prazo", str(v)); d = "prazo=%d" % v
        elif a == "fin":
            pg.click("label[for=sit-financiado]"); d = "financiado"
        elif a == "quit":
            pg.click("label[for=sit-quitado]"); d = "quitado"
        elif a == "slider_i":
            v = rnd.randint(100000, 5000000)
            pg.evaluate("v=>{const r=document.getElementById('range-imovel');r.value=v;r.dispatchEvent(new Event('input',{bubbles:true}))}", v); d = "slider imovel %d" % v
        elif a == "slider_r":
            v = rnd.randint(50000, 3000000)
            pg.evaluate("v=>{const r=document.getElementById('range-receber');r.value=v;r.dispatchEvent(new Event('input',{bubbles:true}))}", v); d = "slider receber %d" % v
        elif a == "conforto":
            v = rnd.choice([0, 1, 500, 3000, 9000, 50000]); pg.fill("#campo-conforto", str(v)); pg.press("#campo-conforto", "Enter"); d = "conforto=%d" % v
        else:
            campo = rnd.choice(["#campo-imovel", "#campo-receber", "#campo-conforto"])
            lixo = rnd.choice(["abc", "", "--", "1e9", "0,0,0", "٣٣٣", "<b>1</b>", "9" * 30, "-5", "1.2.3.4", " "])
            pg.fill(campo, lixo); pg.press(campo, "Enter"); d = "lixo %s em %s" % (lixo[:8], campo)
        histor.append(d)
        invariantes(pg, "%s#%d" % (nome, k), d)
    pg.wait_for_timeout(600)
    # o endereço reabre a mesma simulação
    e = estado(pg)
    pg2 = ctx.new_page()
    pg2.goto(e["url"])
    pg2.wait_for_selector("#alts .alt")
    e2 = estado(pg2)
    for k in ("parcela", "total", "credito", "imovel", "receber", "anos"):
        confere("[%s] link compartilhado reabre igual: %s" % (nome, k), e[k] == e2[k], (e[k], e2[k]))
    confere("[%s] sem erro de JS" % nome, not erros, erros[:3])
    ctx.close()


def casos_fixos(nav):
    ctx = nav.new_context(viewport={"width": 1100, "height": 900})
    ctx.route("**/*umami*", lambda r: r.abort())
    pg = ctx.new_page()
    pg.goto("http://127.0.0.1:%d/" % PORTA); pg.wait_for_selector("#alts .alt")
    def setv(sel, v):
        pg.fill(sel, f"{v:,}".replace(",", ".")); pg.press(sel, "Enter")
    # "outro valor trava?" -> pedido preservado ao baixar e subir o imóvel
    setv("#campo-imovel", 1_000_000); setv("#campo-receber", 500_000)
    setv("#campo-imovel", 600_000)
    e = estado(pg); confere("baixar imóvel ajusta receber ao limite", num(e["receber"]) == 360_000, e["receber"])
    setv("#campo-imovel", 1_000_000)
    e = estado(pg); confere("subir imóvel devolve o valor pedido (não trava)", num(e["receber"]) == 500_000, e["receber"])
    # ajustar receber manualmente depois de ter sido limitado: vale o novo
    setv("#campo-imovel", 600_000); setv("#campo-receber", 200_000); setv("#campo-imovel", 1_000_000)
    e = estado(pg); confere("pedido novo substitui o antigo", num(e["receber"]) == 200_000, e["receber"])
    # financiado: saldo e receber
    pg.click("label[for=sit-financiado]"); setv("#campo-saldo", 300_000); setv("#campo-receber", 400_000)
    e = estado(pg); confere("saldo 300k + receber 400k = 700k (70%) é cortado em 600k", num(e["receber"]) == 300_000, e["receber"])
    pg.click("label[for=sit-quitado]")
    e = estado(pg); confere("voltar a quitado devolve limite cheio, receber pedido 400k", num(e["receber"]) == 400_000 and num(e["saldo"]) == 0, (e["receber"], e["saldo"]))
    # prazo não mexe em receber
    pg.select_option("#sel-prazo", "5")
    e = estado(pg); confere("prazo não altera o valor a receber", num(e["receber"]) == 400_000, e["receber"])
    # teto de R$ 3 mi
    setv("#campo-imovel", 10_000_000); setv("#campo-receber", 3_500_000)
    e = estado(pg); confere("teto de crédito de R$ 3 mi", num(e["receber"]) == 3_000_000 and "teto" in e["rotLim"], (e["receber"], e["rotLim"]))
    # mínimo
    setv("#campo-receber", 10_000)
    e = estado(pg); confere("mínimo de R$ 50 mil", num(e["receber"]) == 50_000, e["receber"])
    print("   cartões com receber no mínimo:", estado(pg)["alts"][1].replace("\n", " | "))
    ctx.close()


def main():
    pasta = os.path.join(AQUI, "paginas_seo")
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORTA), functools.partial(H, directory=pasta))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    with sync_playwright() as pw:
        for nome in ("chromium", "webkit"):
            nav = getattr(pw, nome).launch()
            casos_fixos(nav)
            for seed in range(4):
                rodar(nav, nome + str(seed), seed, 70)
            nav.close()
    srv.shutdown()
    vistos = set()
    print("\n%d falha(s)" % len(FALHAS))
    for n, d in FALHAS:
        k = re.sub(r"^\[[^\]]*\] [^|]*\| ", "", n)
        if k not in vistos:
            vistos.add(k); print(" -", n, d)


main()
