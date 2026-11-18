import datetime
import json

import conteudo
import gerador_homeequity as g


def _gerar(pasta, hoje, manifesto):
    g.gerar_site(str(pasta), hoje=hoje, manifesto=str(manifesto))
    return json.loads(manifesto.read_text(encoding="utf-8"))


def test_data_so_muda_quando_o_conteudo_muda(tmp_path, monkeypatch):
    man = tmp_path / "datas.json"
    d1, d2 = datetime.date(2026, 11, 18), datetime.date(2026, 11, 25)
    primeiro = _gerar(tmp_path / "a", d1, man)
    assert {v["data"] for v in primeiro.values()} == {"2026-11-18"}
    segundo = _gerar(tmp_path / "b", d2, man)
    assert segundo == primeiro  # nada mudou: as datas ficam
    monkeypatch.setattr(conteudo, "ATUALIZACOES", conteudo.ATUALIZACOES + [("25/11/2026", "teste")])
    terceiro = _gerar(tmp_path / "c", d2, man)
    assert terceiro["atualizacoes"]["data"] == "2026-11-25"
    assert terceiro["sobre"]["data"] == "2026-11-18"
