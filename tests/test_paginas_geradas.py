import datetime
import json
import os
import re

import pytest

import calculo
import conteudo
import gerador_homeequity as g

HOJE = datetime.date(2026, 11, 18)


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("site")
    g.gerar_site(str(pasta), hoje=HOJE)
    return str(pasta)


def _ler(site, nome):
    with open(os.path.join(site, nome), encoding="utf-8") as f:
        return f.read()


def _html(site):
    nomes = ["index.html"] + [pg["slug"] + ".html" for pg in conteudo.PAGINAS]
    return {n: _ler(site, n) for n in nomes}


def test_gera_todas_as_paginas_e_arquivos(site):
    for n in ["index.html", "404.html", "styles.css", "calculo.js", "simulador.js", "menu.js", "sitemap.xml", "robots.txt", "llms.txt", "feed.xml",
              "_headers", "favicon.ico", "og-image.png", ".well-known/security.txt", "dados/taxas-referencia.csv", g.indexnow.CHAVE + ".txt"]:
        assert os.path.exists(os.path.join(site, n)), n
    for pg in conteudo.PAGINAS:
        assert os.path.exists(os.path.join(site, pg["slug"] + ".html"))


def test_cada_pagina_tem_titulo_curto_h1_unico_e_canonical(site):
    for nome, html in _html(site).items():
        titulo = re.search(r"<title>(.*?)</title>", html).group(1)
        assert 10 < len(titulo) <= 60, (nome, len(titulo), titulo)
        assert html.count("<h1") == 1, nome
        slug = "" if nome == "index.html" else nome[:-5]
        assert 'rel="canonical" href="' + g.DOMINIO + "/" + slug + '"' in html, nome
        assert 'lang="pt-BR"' in html


def test_sem_marcador_sem_style_inline_e_sem_script_inline(site):
    for nome, html in _html(site).items():
        assert "@@" not in html, nome
        assert not re.search(r"<[a-z]+[^>]*\sstyle=", html), nome  # a CSP não permite
        for m in re.finditer(r"<script([^>]*)>", html):
            assert "src=" in m.group(1) or "application/ld+json" in m.group(1), (nome, m.group(0))
        assert not re.search(r"\son[a-z]+=", html), nome


def test_titulos_e_descricoes_nao_se_repetem(site):
    titulos, descricoes = [], []
    for html in _html(site).values():
        titulos.append(re.search(r"<title>(.*?)</title>", html).group(1))
        descricoes.append(re.search(r'name="description" content="(.*?)"', html).group(1))
    assert len(set(titulos)) == len(titulos)
    assert len(set(descricoes)) == len(descricoes)


def test_link_do_parceiro_so_no_botao_da_confirmacao(site):
    total = 0
    for nome, html in _html(site).items():
        n = html.count(g.LINK_PARCEIRO)
        total += n
        assert n == (1 if nome == "index.html" else 0), nome
    assert total == 1
    home = _ler(site, "index.html")
    assert re.search(r'<a class="btn" id="a-parceiro" href="' + re.escape(g.LINK_PARCEIRO) + r'" target="_blank" rel="noopener sponsored">', home)
    assert g.LINK_PARCEIRO.startswith("https://proposta.api.br/f/")


def test_sem_texto_de_remuneracao_nem_ranking(site):
    proibidas = ["comissão", "comissao", "remuneração", "remuneracao", "recomendado", "melhor banco", "aprovação garantida"]
    for nome, html in _html(site).items():
        baixo = re.sub(r"<[^>]+>", " ", html).lower()
        for t in proibidas:
            assert t not in baixo, (nome, t)
        assert baixo.count("ranking") == baixo.count("não fazemos ranking"), nome  # só para dizer que não fazemos


def test_nao_cita_instituicao_nem_parceiro_pelo_nome(site):
    for nome, html in _html(site).items():
        baixo = html.lower()
        for t in ("financia tudo", "financiatudo", "credicto", "finafaz"):
            assert t not in baixo, (nome, t)


def test_umami_so_entra_com_id(site, monkeypatch, tmp_path):
    assert "umami" not in _ler(site, "index.html").lower() or g.UMAMI_ID
    monkeypatch.setattr(g, "UMAMI_ID", "abc-123")
    g.gerar_site(str(tmp_path), hoje=HOJE)
    assert 'data-website-id="abc-123"' in _ler(str(tmp_path), "index.html")


def test_csp_permite_so_o_necessario(site):
    h = _ler(site, "_headers")
    assert "script-src 'self' https://static.cloudflareinsights.com https://cloud.umami.is;" in h
    assert "style-src 'self';" in h
    assert "object-src 'none'" in h and "frame-ancestors 'none'" in h
    assert "triagem" not in h and "unsafe-inline" not in h


def test_links_internos_existem(site):
    existentes = {"/"} | {"/" + pg["slug"] for pg in conteudo.PAGINAS} | {"/feed.xml", "/dados/taxas-referencia.csv"}
    for nome, html in _html(site).items():
        for href in re.findall(r'href="(/[^"#?]*)', html):
            if href.startswith("/fonts") or href.endswith((".png", ".ico", ".css")):
                continue
            assert href in existentes, (nome, href)


def test_ids_unicos_e_ancoras_resolvem(site):
    html = _ler(site, "index.html")
    ids = re.findall(r'\sid="([^"]+)"', html)
    assert len(ids) == len(set(ids))
    for ancora in re.findall(r'href="#([^"]+)"', html):
        assert ancora in ids, ancora


def test_home_mostra_a_simulacao_padrao_calculada(site):
    html = _ler(site, "index.html")
    ref = conteudo._ref()
    i = calculo.taxa_mensal(ref["ipca12m"])
    r = calculo.simular(800_000, 250_000, 0, 180, i)
    assert 'id="r-parcela">' + conteudo.brl0(r["parcela"]) + "<" in html
    assert 'id="r-total">' + conteudo.brl0(r["total"]) + "<" in html
    assert conteudo.pct(i * 100) + " a.m." in html
    assert "Faça sua proposta" in html and "Consultar opções" in html
    assert "opções reais" not in html


def test_home_tem_json_ld_valido(site):
    html = _ler(site, "index.html")
    blocos = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    assert len(blocos) == 2
    for b in blocos:
        json.loads(b)
    faq = json.loads(blocos[1])
    assert len(faq["mainEntity"]) == len(conteudo.FAQ)


def test_sitemap_lista_todas_as_paginas_indexaveis(site):
    sm = _ler(site, "sitemap.xml")
    for c in g.PAGINAS_INDEXAVEIS:
        assert "<loc>" + g.DOMINIO + c + "</loc>" in sm
    assert sm.count("<url>") == len(g.PAGINAS_INDEXAVEIS)
    assert "/privacidade" not in sm and "/termos" not in sm
    assert "Sitemap: " + g.DOMINIO + "/sitemap.xml" in _ler(site, "robots.txt")


def test_numeros_dos_textos_vem_do_calculo(site):
    cm = _ler(site, "como-funciona.html")
    r = calculo.simular(800_000, 250_000, 0, 180, conteudo.taxa_ref())
    assert conteudo.brl0(r["parcela"]) in cm and conteudo.brl0(r["total"]) in cm
    tx = _ler(site, "taxas-de-referencia.html")
    assert "SGS 29976" in tx and "SGS 13522" in tx and "1,09%" in tx


def test_calculo_js_publicado_e_o_gerado(site):
    assert _ler(site, "calculo.js") == g.gerar_calculo_js()
    html = _ler(site, "index.html")
    assert re.search(r'/calculo\.js\?v=[0-9a-f]{10}"', html) and re.search(r'/simulador\.js\?v=[0-9a-f]{10}"', html)


def test_tem_acessibilidade_basica(site):
    html = _ler(site, "index.html")
    assert 'class="skip"' in html
    assert html.count("<main") == 1
    for rotulo in ("campo-imovel", "campo-receber", "campo-prazo", "campo-conforto", "campo-saldo"):
        assert 'for="' + rotulo + '"' in html, rotulo
    assert '<dialog id="dlg-confirma" aria-labelledby="dlg-titulo">' in html


def test_tabelas_tem_rotulo_por_celula_para_o_celular(site):
    """No celular o CSS empilha cada linha em cartão e lê o rótulo de data-l; sem ele os números perdem o nome da coluna."""
    for nome in ("home-equity-ou-outro-credito.html", "taxas-de-referencia.html", "custos-alem-dos-juros.html"):
        html = _ler(site, nome)
        assert "<td>" not in html, nome
        assert 'data-l="' in html, nome


def test_endereco_da_barra_nao_leva_ancora():
    """Com '#simulador' na barra, o Safari volta para o topo do simulador ao voltar de uma página interna; só o link copiado leva a âncora."""
    with open(os.path.join("src", "simulador.js"), encoding="utf-8") as f:
        js = f.read()
    assert "replaceState(null, '', enderecoDaSimulacao(false))" in js
    assert js.count("enderecoDaSimulacao(true)") == 1


def test_js_nao_mexe_em_estilo_inline():
    """A CSP (style-src 'self') não aceita estilo inline e o Safari avisa até de CSSOM: o JS só pode usar atributos e classes."""
    for nome in ("simulador.js", "menu.js"):
        with open(os.path.join("src", nome), encoding="utf-8") as f:
            js = f.read()
        js = re.sub(r"/\*.*?\*/", "", js, flags=re.S)
        js = re.sub(r"//[^\n]*", "", js)
        for proibido in (".style.", "cssText", "setAttribute('style'", 'setAttribute("style"', "insertRule", "innerHTML"):
            assert proibido not in js, (nome, proibido)


def _json_ld(html):
    return [json.loads(b) for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)]


def test_organizacao_tem_logo_e_paginas_internas_tem_trilha(site):
    home = _json_ld(_ler(site, "index.html"))
    org = [n for blk in home for n in blk.get("@graph", []) if n.get("@type") == "Organization"][0]
    assert org["logo"]["url"].endswith("/apple-touch-icon.png") and org["logo"]["width"] >= 112
    for slug in ("como-funciona", "metodologia", "privacidade", "dados-abertos"):
        trilha = [b for b in _json_ld(_ler(site, slug + ".html")) if b["@type"] == "BreadcrumbList"]
        assert len(trilha) == 1, slug
        itens = trilha[0]["itemListElement"]
        assert [i["position"] for i in itens] == [1, 2] and itens[1]["item"].endswith("/" + slug)


def test_dados_abertos_tem_dataset_e_link_para_o_csv(site):
    html = _ler(site, "dados-abertos.html")
    ds = [b for b in _json_ld(html) if b["@type"] == "Dataset"]
    assert len(ds) == 1
    d = ds[0]
    assert d["license"].startswith("https://opendatacommons.org/") and d["isAccessibleForFree"] is True
    assert d["distribution"][0]["contentUrl"] == "https://homeequity.datalabglobal.com/dados/taxas-referencia.csv"
    assert "/" in d["temporalCoverage"] and d["variableMeasured"]
    assert 'href="/dados/taxas-referencia.csv"' in html and "ODbL 1.0" in html and "Como citar" in html
    assert "/dados-abertos" in _ler(site, "sitemap.xml")


def test_termos_de_busca_aparecem_onde_o_assunto_ja_e_esse(site):
    assert "empréstimo com garantia de imóvel" in _ler(site, "como-funciona.html")
    comp = _ler(site, "home-equity-ou-outro-credito.html")
    assert "empréstimo com garantia de imóvel" in comp and "refinanciamento" in comp and "portabilidade" in comp
    assert "crédito com garantia de imóvel" in _ler(site, "como-funciona.html")


def test_descricoes_das_paginas_pequenas_nao_sao_curtas(site):
    for slug in ("sobre", "atualizacoes", "privacidade", "termos"):
        desc = re.search(r'name="description" content="(.*?)"', _ler(site, slug + ".html")).group(1)
        assert len(desc) >= 100, (slug, len(desc))


def test_js_com_versao_no_endereco_tem_cache_imutavel():
    for nome in ("calculo.js", "simulador.js", "menu.js"):
        trecho = g.HEADERS.split("/" + nome)[1].split("\n\n")[0]
        assert "immutable" in trecho, nome


def test_privacidade_e_termos_ficam_fora_do_indice(site):
    for slug in ("privacidade", "termos"):
        h = _ler(site, slug + ".html")
        assert 'name="robots" content="noindex,follow"' in h, slug
    assert 'name="robots" content="index,follow' in _ler(site, "como-funciona.html")


def test_home_declara_o_simulador_como_aplicacao_web(site):
    h = _ler(site, "index.html")
    assert '"@type": "WebApplication"' in h and '"applicationCategory": "FinanceApplication"' in h and '"price": "0"' in h
