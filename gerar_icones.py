"""Gera os ícones (favicon, apple-touch-icon) e a imagem de compartilhamento (og-image.png) a partir do logo em SVG de layout.py.

Precisa do Playwright e do Pillow; roda na máquina do dono, fora do CI. Os arquivos gerados ficam em paginas_seo/ e são versionados.
Uso: python gerar_icones.py
"""
import io
import os

from PIL import Image
from playwright.sync_api import sync_playwright

import layout

AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, "paginas_seo")
AC = "#4aa3b5"


def _svg(tamanho):
    s = layout.LOGO.replace('<span class="tile">', "").replace("</span>", "")
    return s.replace('width="32" height="32"', 'width="%d" height="%d"' % (tamanho, tamanho))


def _icone_html(lado):
    return ("<html><body style='margin:0;background:transparent'><div style='width:%dpx;height:%dpx;border-radius:%dpx;display:grid;place-items:center;color:%s;"
            "background:linear-gradient(145deg,#0b2a33,#06101c);border:%dpx solid rgba(74,163,181,.55);box-sizing:border-box'>%s</div></body></html>"
            % (lado, lado, lado * 0.26, AC, max(1, lado // 40), _svg(int(lado * 0.72))))


def _og_html():
    with open(os.path.join(AQUI, "src", "og-image.html"), encoding="utf-8") as f:
        return f.read().replace("@@LOGO@@", _svg(120))


def main():
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for nome, lado in (("favicon-32.png", 32), ("favicon-192.png", 192), ("apple-touch-icon.png", 180), ("icone-256.png", 256)):
            pg = b.new_page(viewport={"width": lado, "height": lado})
            pg.set_content(_icone_html(lado))
            pg.screenshot(path=os.path.join(SAIDA, nome), omit_background=(nome != "apple-touch-icon.png"))
            pg.close()
        pg = b.new_page(viewport={"width": 1200, "height": 630})
        pg.set_content(_og_html())
        pg.wait_for_timeout(300)
        pg.screenshot(path=os.path.join(SAIDA, "og-image.png"))
        b.close()
    img = Image.open(os.path.join(SAIDA, "icone-256.png")).convert("RGBA")
    img.save(os.path.join(SAIDA, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])
    os.remove(os.path.join(SAIDA, "icone-256.png"))


if __name__ == "__main__":
    main()
