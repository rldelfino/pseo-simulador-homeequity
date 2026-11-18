"""A conta do navegador (calculo.js) precisa dar o mesmo resultado que calculo.py. Usa o Node; sem Node o teste é pulado."""
import json
import os
import shutil
import subprocess

import pytest

import calculo as c
import gerador_homeequity as g

NODE = shutil.which("node")
pytestmark = pytest.mark.skipif(NODE is None, reason="Node não instalado")

CASOS = [(800_000, 250_000, 0, 180), (150_000, 30_000, 0, 60), (3_000_000, 1_000_000, 0, 240), (500_000, 50_000, 200_000, 120),
         (1_250_000, 400_000, 100_000, 96), (200_000, 120_000, 0, 144), (10_000_000, 2_900_000, 0, 180), (8_000_000, 1_500_000, 600_000, 120)]


def _rodar(tmp_path, caso, ipca):
    js = tmp_path / "calculo.js"
    js.write_text(g.gerar_calculo_js(), encoding="utf-8")
    prog = ("const H=require(%s);const i=H.taxaMensal(%r);const [im,re,sa,me]=%s;"
            "console.log(JSON.stringify({i:i,r:H.simular(im,re,sa,me,i),alvo:H.receberParaParcela(3000,sa,me,i,5000)}))") % (json.dumps(str(js)), ipca, json.dumps(caso))
    out = subprocess.run([NODE, "-e", prog], capture_output=True, text=True, check=True, timeout=30).stdout
    return json.loads(out)


@pytest.mark.parametrize("caso", CASOS)
@pytest.mark.parametrize("ipca", [0.0, 4.63, 9.1])
def test_js_igual_ao_python(tmp_path, caso, ipca):
    im, re_, sa, me = caso
    r = _rodar(tmp_path, caso, ipca)
    i = c.taxa_mensal(ipca)
    py = c.simular(im, re_, sa, me, i)
    assert r["i"] == pytest.approx(i, rel=1e-12)
    for k in ("credito", "parcela", "total", "juros", "ltv", "limite"):
        assert r["r"][k] == pytest.approx(py[k], rel=1e-9)
    assert r["r"]["acimaLimite"] == py["acima_limite"]
    assert r["alvo"] == c.receber_para_parcela(3000, im, sa, me, i)


def test_calculo_js_tem_as_referencias_do_bcb(tmp_path):
    texto = g.gerar_calculo_js()
    assert "ipca12m" in texto and "garantiaRealAm" in texto
    assert "@@" not in texto
