"""Varredura em celulares e tablets (fora do CI). Uso: python varredura_dispositivos.py (capturas em graphify-out/)"""
import functools, http.server, os, sys, threading, json
from playwright.sync_api import sync_playwright

AQUI = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(AQUI, "graphify-out")
PORTA = 8812
SLUGS = ["", "como-funciona", "garantia-do-imovel", "custos-alem-dos-juros", "home-equity-ou-outro-credito", "quando-nao-vale-a-pena",
         "taxas-de-referencia", "metodologia", "sobre", "atualizacoes", "privacidade", "termos", "pagina-que-nao-existe"]
ACHADOS = []


def achado(tag, msg):
    ACHADOS.append(tag + " :: " + msg)
    print("ACHADO", tag, "::", msg)


class S(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        p = super().translate_path(path.split("?")[0])
        if not os.path.exists(p) and os.path.exists(p + ".html"):
            return p + ".html"
        return p

    def log_message(self, *a):
        pass

    def send_error(self, code, message=None, explain=None):
        if code == 404 and os.path.exists(os.path.join(AQUI, "paginas_seo", "404.html")):
            self.send_response(404)
            data = open(os.path.join(AQUI, "paginas_seo", "404.html"), "rb").read()
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            super().send_error(code, message, explain)


JS_AUDIT = """() => {
  const out = {pequenos: [], estourando: [], fontes: []};
  const vis = e => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e); return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none'; };
  document.querySelectorAll('a[href],button,input:not([type=radio]):not([type=range]),select,summary,label[for]').forEach(e => {
    if (!vis(e)) return;
    const r = e.getBoundingClientRect();
    const inline = getComputedStyle(e).display === 'inline' && e.tagName === 'A' && e.closest('p,li,.hint,.fine2,.dim,td');
    if (!inline && (r.height < 40 || r.width < 40) ) out.pequenos.push((e.id || e.className || e.tagName) + ' ' + e.textContent.trim().slice(0, 25) + ' ' + Math.round(r.width) + 'x' + Math.round(r.height));
  });
  document.querySelectorAll('input[type=text],input:not([type]),select,textarea').forEach(e => {
    if (!vis(e)) return;
    const fs = parseFloat(getComputedStyle(e).fontSize);
    if (fs < 16) out.fontes.push((e.id || e.tagName) + ' ' + fs);
  });
  const W = window.innerWidth;
  document.querySelectorAll('body *').forEach(e => {
    if (!vis(e)) return;
    const r = e.getBoundingClientRect();
    if (r.right > W + 1 || r.left < -1) { if (!e.closest('svg') && !e.closest('.sr') && !e.closest('.skip')) out.estourando.push((e.id || e.className || e.tagName) + ' ' + Math.round(r.left) + '..' + Math.round(r.right)); }
  });
  out.overflowX = document.documentElement.scrollWidth - window.innerWidth;
  return out;
}"""


def varrer(pw, nome_nav, dispositivo, base):
    disp = pw.devices[dispositivo]
    nav = getattr(pw, nome_nav).launch()
    ctx = nav.new_context(**disp)
    ctx.route("**/*umami*", lambda r: r.abort())
    tag = dispositivo
    pg = ctx.new_page()
    erros = []
    pg.on("console", lambda m: erros.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: erros.append("PAGEERROR " + str(e)))
    larg = disp["viewport"]["width"]
    for slug in SLUGS:
        resp = pg.goto(base + "/" + slug)
        pg.wait_for_timeout(250)
        if slug.startswith("pagina-"):
            erros.clear()
        a = pg.evaluate(JS_AUDIT)
        t = tag + " /" + slug
        if a["overflowX"] > 0:
            achado(t, "rolagem horizontal de %dpx" % a["overflowX"])
        if a["estourando"]:
            achado(t, "elementos fora da tela: " + "; ".join(a["estourando"][:6]))
        if slug == "":
            if a["fontes"]:
                achado(t, "campo com fonte < 16px (iOS dá zoom): " + ", ".join(a["fontes"]))
            if a["pequenos"]:
                achado(t, "alvos de toque pequenos: " + "; ".join(a["pequenos"][:12]))
            pg.screenshot(path=os.path.join(SHOTS, "v-" + tag.replace(" ", "_") + ".png"), full_page=True)
    # Diálogo
    pg.goto(base + "/")
    pg.wait_for_selector("#alts .alt")
    pg.click("#btn-cta")
    pg.wait_for_timeout(200)
    r = pg.evaluate("(() => {const d=document.getElementById('dlg-confirma').getBoundingClientRect(); return [d.top, d.bottom, innerHeight, d.left, d.right, innerWidth]})()")
    if r[0] < 0 or r[1] > r[2] + 1 or r[3] < 0 or r[4] > r[5] + 1:
        achado(tag, "diálogo não cabe na tela: %s" % r)
    pg.screenshot(path=os.path.join(SHOTS, "d-" + tag.replace(" ", "_") + ".png"))
    # clique na borda interna (padding) do diálogo não pode fechar
    box = pg.evaluate("(() => {const d=document.getElementById('dlg-confirma').getBoundingClientRect(); return [d.left, d.top, d.width, d.height]})()")
    pg.mouse.click(box[0] + 8, box[1] + 8)
    if not pg.is_visible("#dlg-confirma"):
        achado(tag, "clicar na borda interna do diálogo fecha a tela (padding conta como fundo)")
        pg.click("#btn-cta")
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(150)
    if pg.is_visible("#dlg-confirma"):
        achado(tag, "Esc não fecha o diálogo")
    foco = pg.evaluate("document.activeElement && (document.activeElement.id || document.activeElement.tagName)")
    if foco != "btn-cta":
        achado(tag, "foco não volta ao botão ao fechar o diálogo (foi para %s)" % foco)
    # Voltar do navegador depois de mexer e visitar uma página
    pg.goto(base + "/")
    pg.wait_for_selector("#alts .alt")
    pg.fill("#campo-receber", "300.000")
    pg.press("#campo-receber", "Enter")
    pg.select_option("#sel-prazo", "10")
    pg.wait_for_timeout(500)
    esperado = pg.inner_text("#r-parcela")
    pg.evaluate("window.scrollTo({top:1400,behavior:\"instant\"})")
    y0 = pg.evaluate("scrollY")
    pg.evaluate("document.querySelector(\"a[href='/como-funciona']\").click()")
    pg.wait_for_url("**/como-funciona")
    pg.go_back()
    pg.wait_for_selector("#alts .alt")
    pg.wait_for_timeout(500)
    if pg.inner_text("#r-parcela") != esperado:
        achado(tag, "ao voltar do guia, a simulação mudou: %s -> %s" % (esperado, pg.inner_text("#r-parcela")))
    y1 = pg.evaluate("scrollY")
    if abs(y1 - y0) > 150:
        achado(tag, "ao voltar do guia, a rolagem não voltou (era %d, ficou %d)" % (y0, y1))
    # Âncora 'entenda abaixo' e voltar
    pg.goto(base + "/")
    pg.wait_for_selector("#alts .alt")
    pg.click("a[href='#garantia']:visible >> nth=0")
    pg.wait_for_timeout(300)
    pg.go_back()
    pg.wait_for_timeout(300)
    if "#garantia" in pg.url:
        achado(tag, "voltar depois da âncora #garantia não desfez a âncora (url %s)" % pg.url)
    # Menu do celular
    if larg < 900:
        pg.goto(base + "/")
        pg.click("details.menu summary")
        pg.wait_for_timeout(150)
        links = pg.locator("details.menu a:visible").count()
        if links < 3:
            achado(tag, "menu do celular com poucos links (%d)" % links)
        with pg.expect_navigation():
            pg.click("details.menu a:visible >> nth=0")
        pg.wait_for_timeout(300)
        if pg.evaluate("document.querySelector('details.menu') && document.querySelector('details.menu').open"):
            achado(tag, "menu continua aberto depois de escolher um link")
    # Teclado numérico / estado de campos vazios
    pg.goto(base + "/")
    pg.wait_for_selector("#alts .alt")
    pg.fill("#campo-imovel", "")
    pg.press("#campo-imovel", "Enter")
    v = pg.input_value("#campo-imovel")
    if not v:
        achado(tag, "campo do imóvel vazio ficou vazio depois do Enter")
    pg.fill("#campo-receber", "abc")
    pg.press("#campo-receber", "Enter")
    pg.wait_for_timeout(200)
    pr = pg.inner_text("#r-parcela")
    if "NaN" in pr or "Infinity" in pr:
        achado(tag, "parcela com valor inválido: " + pr)
    pg.fill("#campo-imovel", "99999999999999999999")
    pg.press("#campo-imovel", "Enter")
    pg.wait_for_timeout(200)
    iv = pg.input_value("#campo-imovel")
    print(tag, "imovel gigante ->", iv, "parcela", pg.inner_text("#r-parcela"))
    # XSS por parâmetros
    pg.goto(base + "/?imovel=<img src=x onerror=alert(1)>&receber=\"><script>alert(1)</script>&prazo=15&conforto=javascript:alert(1)")
    pg.wait_for_selector("#alts .alt")
    if pg.evaluate("document.querySelectorAll('img[src=x]').length") != 0:
        achado(tag, "XSS por parâmetro")
    if erros:
        achado(tag, "erros no console: " + "; ".join(erros[:4]))
    ctx.close()
    nav.close()


def main():
    pasta = os.path.join(AQUI, "paginas_seo")
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORTA), functools.partial(S, directory=pasta))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d" % PORTA
    alvos = [("webkit", "iPhone SE"), ("webkit", "iPhone 13"), ("webkit", "iPhone 15 Pro Max"), ("webkit", "iPhone 13 landscape"), ("webkit", "iPad Mini"),
             ("chromium", "Pixel 7"), ("chromium", "Galaxy S9+"), ("chromium", "Galaxy S9+ landscape"), ("chromium", "Pixel 5")]
    with sync_playwright() as pw:
        for nav, d in alvos:
            if d not in pw.devices:
                print("sem perfil", d)
                continue
            try:
                varrer(pw, nav, d, base)
            except Exception as e:
                achado(d, "EXCEÇÃO no teste: " + str(e)[:300])
    srv.shutdown()
    print("\n%d achado(s)" % len(ACHADOS))


if __name__ == "__main__":
    main()
