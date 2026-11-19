import pytest

import calculo as c


def test_pmt_exemplo_do_desenho():
    i = c.taxa_mensal(4.63)
    assert i == pytest.approx(0.014720, abs=1e-6)
    r = c.simular(800_000, 250_000, 0, 180, i)
    assert round(r["parcela"]) == 3966
    assert round(r["total"]) == 713837
    assert r["ltv"] == pytest.approx(0.3125)
    assert not r["acima_limite"]


def test_taxa_com_ipca_zero_e_so_a_do_parceiro():
    assert c.taxa_mensal(0) == pytest.approx(0.0109)


def test_parcela_com_taxa_zero_divide_igual():
    assert c.pmt(120_000, 0, 120) == 1000


def test_valor_presente_e_inverso_do_pmt():
    i = 0.0147
    assert c.valor_presente(c.pmt(200_000, i, 120), i, 120) == pytest.approx(200_000)


def test_saldo_entra_no_credito_e_no_limite():
    r = c.simular(500_000, 50_000, 200_000, 120, 0.015)
    assert r["credito"] == 250_000
    assert r["limite"] == 300_000
    assert not r["acima_limite"]
    assert c.simular(500_000, 120_000, 200_000, 120, 0.015)["acima_limite"]
    assert c.receber_maximo(500_000, 200_000) == 100_000
    assert c.receber_maximo(500_000, 400_000) == 0


def test_receber_para_parcela_cabe_na_parcela_alvo():
    i = 0.0147
    v = c.receber_para_parcela(3000, 800_000, 0, 180, i)
    assert v % 5000 == 0
    assert c.pmt(v, i, 180) <= 3000
    assert c.pmt(v + 5000, i, 180) > 3000


def test_prazo_invalido():
    with pytest.raises(ValueError):
        c.pmt(1000, 0.01, 0)


def test_limites_do_parceiro_divulgados():
    assert c.LTV_MAX == 0.60
    assert c.PRAZO_MAX_MESES == 240
    assert c.PRAZO_MAX_ANOS * 12 == c.PRAZO_MAX_MESES and 1 <= c.PRAZO_MIN_ANOS < c.PRAZO_MAX_ANOS


def test_teto_de_credito_da_ferramenta():
    assert c.CREDITO_MAX == 3_000_000
    assert c.limite_credito(1_000_000) == 600_000          # 60% vale abaixo do teto
    assert c.limite_credito(10_000_000) == 3_000_000       # acima, o teto vale
    assert c.receber_maximo(10_000_000, 500_000) == 2_500_000
    assert c.simular(10_000_000, 3_100_000, 0, 180, 0.0147)["acima_limite"] is True
