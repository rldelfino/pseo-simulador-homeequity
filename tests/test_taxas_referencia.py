import datetime

import pytest

import etl_taxas as etl
import taxas_referencia as tr


def test_csv_tem_as_series_do_simulador():
    linhas = tr.ler()
    for codigo in (tr.CODIGO_IPCA, tr.CODIGO_GARANTIA_REAL, *tr.CODIGOS_COMPARACAO):
        assert tr.ultima(codigo, linhas), "falta a série %d" % codigo


def test_garantia_real_e_mais_barata_que_as_sem_garantia():
    linhas = tr.ler()
    gar = tr.ao_mes(tr.ultima(29976, linhas))
    for c in (20742, 20741, 22022):
        assert gar < tr.ao_mes(tr.ultima(c, linhas))


def test_mensal_equivalente():
    assert tr.mensal_equivalente(0) == 0
    assert tr.mensal_equivalente(12.682503) == pytest.approx(1.0, abs=1e-5)


def test_ao_mes_respeita_a_unidade():
    assert tr.ao_mes({"valor": 2.14, "unidade": "am"}) == 2.14
    assert tr.ao_mes({"valor": 110.94, "unidade": "aa"}) == pytest.approx(6.42, abs=0.01)


def test_salvar_e_ler_ida_e_volta(tmp_path):
    f = tmp_path / "t.csv"
    linhas = [{"codigo": 29976, "modalidade": "x", "mes": "2026-09", "valor": 2.14, "unidade": "am"}]
    tr.salvar(linhas, str(f))
    assert tr.ler(str(f)) == linhas
    assert tr.ler(str(tmp_path / "nao-existe.csv")) == []


def test_etl_mantem_o_csv_se_a_rede_falha(tmp_path):
    f = tmp_path / "t.csv"
    tr.salvar([{"codigo": 29976, "modalidade": "x", "mes": "2026-09", "valor": 2.14, "unidade": "am"}], str(f))

    def get(*a, **k):
        raise etl.requests.RequestException("sem rede")
    assert etl.atualizar(str(f), hoje=datetime.date(2026, 11, 18), get=get) == {}
    assert len(tr.ler(str(f))) == 1


def test_etl_descarta_valor_fora_da_faixa_plausivel():
    class R:
        def raise_for_status(self): pass
        def json(self): return [{"data": "01/09/2026", "valor": "2.14"}, {"data": "01/08/2026", "valor": "999"}, {"data": "01/07/2026", "valor": "x"}]
    pontos = etl.buscar_serie(tr.serie_def(29976), datetime.date(2026, 1, 1), datetime.date(2026, 11, 1), get=lambda *a, **k: R())
    assert pontos == [("2026-09", 2.14)]


def test_etl_rejeita_resposta_que_nao_e_lista():
    class R:
        def raise_for_status(self): pass
        def json(self): return {"erro": 1}
    with pytest.raises(ValueError):
        etl.buscar_serie(tr.serie_def(29976), datetime.date(2026, 1, 1), datetime.date(2026, 11, 1), get=lambda *a, **k: R())


def test_gerador_recusa_taxa_fora_da_faixa(monkeypatch):
    """Se o CSV vier adulterado (IPCA de 99999%), o site não é gerado."""
    import conteudo
    linhas = tr.ler()
    ruim = [dict(l, valor=99999.0) if l["codigo"] == tr.CODIGO_IPCA else l for l in linhas]
    monkeypatch.setattr(tr, "ler", lambda *a, **k: ruim)
    with pytest.raises(ValueError):
        conteudo._ref()
