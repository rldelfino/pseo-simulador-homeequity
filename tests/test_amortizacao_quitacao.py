"""Amortização ano a ano e cenário "quitar dívida cara": conta em Python, igualdade com o JS (Node) e números escritos na home."""
import datetime
import json
import os
import shutil
import subprocess

import pytest

import calculo as c
import conteudo
import gerador_homeequity as g

NODE = shutil.which("node")
HOJE = datetime.date(2026, 11, 18)


@pytest.mark.parametrize("credito,meses,i", [(250_000, 180, 0.0147), (60_000, 60, 0.02), (3_000_000, 240, 0.0109), (100_000, 96, 0.0)])
def test_amortizacao_fecha_em_zero_e_soma_certo(credito, meses, i):
    linhas = c.amortizacao_anual(credito, i, meses)
    assert len(linhas) == meses // 12
    assert linhas[-1]["saldo"] == 0
    assert sum(x["amortizacao"] for x in linhas) == pytest.approx(credito, rel=1e-9)
    total = c.pmt(credito, i, meses) * meses
    assert sum(x["juros"] for x in linhas) == pytest.approx(total - credito, rel=1e-9, abs=1e-6)
    saldos = [x["saldo"] for x in linhas]
    assert saldos == sorted(saldos, reverse=True)
    juros = [x["juros"] for x in linhas]
    assert juros == sorted(juros, reverse=True)  # os juros do ano só caem


def test_amortizacao_prazo_que_nao_e_multiplo_de_12():
    linhas = c.amortizacao_anual(100_000, 0.01, 30)
    assert len(linhas) == 3 and linhas[-1]["saldo"] == 0


def test_comparar_quitacao_mesma_taxa_nao_tem_economia():
    r = c.comparar_quitacao(60_000, 0.0147, 180, 0.0147)
    assert r["economia_mes"] == pytest.approx(0, abs=1e-9) and r["economia_total"] == pytest.approx(0, abs=1e-6)


def test_comparar_quitacao_taxa_maior_gera_economia():
    r = c.comparar_quitacao(60_000, 0.0642, 180, 0.0147)
    assert r["parcela_atual"] > r["parcela_he"] > 0
    assert r["economia_total"] == pytest.approx(r["total_atual"] - r["total_he"], rel=1e-9)
    assert r["juros_mes1"] == pytest.approx(60_000 * 0.0642)


def test_referencias_tem_as_medias_das_dividas():
    ref = g.referencias()
    for chave in ("pessoal", "cheque", "rotativo"):
        assert 0.5 < ref[chave + "Am"] < 30 and ref[chave + "Mes"]
    assert ref["rotativoAm"] > ref["chequeAm"] > ref["pessoalAm"] > ref["garantiaRealAm"]


@pytest.mark.skipif(NODE is None, reason="Node não instalado")
@pytest.mark.parametrize("credito,meses,i", [(250_000, 180, 0.0147), (60_000, 60, 0.02), (3_000_000, 240, 0.0109)])
def test_js_igual_ao_python(tmp_path, credito, meses, i):
    js = tmp_path / "calculo.js"
    js.write_text(g.gerar_calculo_js(), encoding="utf-8")
    prog = ("const H=require(%s);console.log(JSON.stringify({a:H.amortizacaoAnual(%r,%r,%r),q:H.compararQuitacao(%r,0.0642,%r,%r)}))"
            % (json.dumps(str(js)), credito, i, meses, credito, meses, i))
    out = json.loads(subprocess.run([NODE, "-e", prog], capture_output=True, text=True, check=True, timeout=30).stdout)
    py = c.amortizacao_anual(credito, i, meses)
    assert len(out["a"]) == len(py)
    for a, b in zip(out["a"], py):
        for k in ("juros", "amortizacao", "saldo"):
            assert a[k] == pytest.approx(b[k], rel=1e-9, abs=1e-6)
    q = c.comparar_quitacao(credito, 0.0642, meses, i)
    for k_js, k_py in (("parcelaAtual", "parcela_atual"), ("totalAtual", "total_atual"), ("jurosMes1", "juros_mes1"), ("parcelaHe", "parcela_he"),
                       ("totalHe", "total_he"), ("economiaMes", "economia_mes"), ("economiaTotal", "economia_total")):
        assert out["q"][k_js] == pytest.approx(q[k_py], rel=1e-9)


@pytest.fixture(scope="module")
def home(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("site")
    g.gerar_site(str(pasta), hoje=HOJE)
    with open(os.path.join(str(pasta), "index.html"), encoding="utf-8") as f:
        return f.read()


def test_home_traz_a_amortizacao_do_cenario_padrao(home):
    ref = g.referencias()
    i = c.taxa_mensal(ref["ipca12m"])
    r = c.simular(800_000, 250_000, 0, 180, i)
    linhas = c.amortizacao_anual(r["credito"], i, 180)
    assert linhas[-1]["saldo"] == 0
    assert home.count('<tbody id="amort-corpo">') == 1
    assert conteudo.amort_linhas(linhas) in home and conteudo.amort_resumo(r, linhas) in home
    assert "Ver a amortização ano a ano" in home and 'id="det-amort"' in home
    assert home.count("<tr><th scope=\"row\">") >= 16  # 15 anos + total


def test_home_traz_o_cenario_de_quitar_divida_padrao(home):
    ref = g.referencias()
    i = c.taxa_mensal(ref["ipca12m"])
    q = c.comparar_quitacao(conteudo.DIVIDA_PADRAO, ref["pessoalAm"] / 100, 180, i)
    assert conteudo.quitar_cartoes(q, ref["pessoalAm"], 15, i * 100) in home
    assert conteudo.quitar_texto(q, 15) in home
    for rotulo in ("Crédito pessoal sem garantia", "Cheque especial", "Cartão de crédito rotativo", "Outra <small>informo a taxa</small>"):
        assert rotulo in home
    assert 'id="btn-usar-divida"' in home and 'for="campo-divida"' in home and 'id="lb-tipodiv"' in home
    assert 'id="bloco-taxa-div" hidden' in home


def test_home_traz_rosca_graficos_faixa_e_prazo_livre(home):
    ref = g.referencias()
    i = c.taxa_mensal(ref["ipca12m"])
    r = c.simular(800_000, 250_000, 0, 180, i)
    assert 'id="rosca-cred"' in home and 'stroke-dasharray="%.1f 289.03"' % (r["credito"] / r["total"] * 289.0265) in home
    assert ("%d%%" % round(r["juros"] / r["total"] * 100)) in home and conteudo.brl0(r["juros"]) in home
    assert 'id="amort-graf"' in home and 'id="q-grafico"' in home and 'class="band fatos"' in home
    assert 'id="campo-prazo"' in home and 'id="range-prazo"' in home and "<select" not in home
    assert 'min="%d" max="%d"' % (c.PRAZO_MIN_ANOS, c.PRAZO_MAX_ANOS) in home
