"""ETL das taxas de referência do Banco Central (SGS) para dados/taxas_referencia.csv.

Idempotente. Falha de rede ou resposta estranha NÃO derruba o pipeline: avisa e sai com código 0, mantendo o CSV que já existe.
A API aceita no máximo 20 valores em "ultimos/N"; por isso pedimos por intervalo de datas. Os valores vêm como texto com ponto decimal e a
data é o primeiro dia do mês de referência.

Uso: python etl_taxas.py
"""
import datetime
import sys

import requests

import taxas_referencia as tr

MESES_HISTORICO = 24
MINIMO_DE_PONTOS = 6
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; datalab-global-etl/1.0; +https://www.datalabglobal.com)"}


def _inicio_da_janela(hoje, meses):
    total = hoje.year * 12 + (hoje.month - 1) - meses
    return datetime.date(total // 12, total % 12 + 1, 1)


def buscar_serie(serie, inicio, fim, get=requests.get):
    """Lista [(aaaa-mm, valor)] da série do SGS entre as datas. Levanta ValueError se a resposta mudou de formato."""
    resp = get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.%d/dados" % serie["codigo"],
               params={"formato": "json", "dataInicial": inicio.strftime("%d/%m/%Y"), "dataFinal": fim.strftime("%d/%m/%Y")},
               headers=HEADERS, timeout=30)
    resp.raise_for_status()
    dados = resp.json()
    if not isinstance(dados, list):
        raise ValueError("resposta do SGS mudou de formato (esperava lista): %r" % (str(dados)[:120],))
    pontos = {}
    for item in dados:
        try:
            dia, mes, ano = item["data"].split("/")
            valor = float(str(item["valor"]).replace(",", "."))
        except (KeyError, ValueError, AttributeError):
            continue
        if not (serie["faixa"][0] <= valor <= serie["faixa"][1]):
            continue  # protege contra série errada
        pontos[ano + "-" + mes] = valor
    return sorted(pontos.items())


def atualizar(caminho=tr.CAMINHO_CSV, hoje=None, get=requests.get):
    """Atualiza o CSV. Devolve {codigo: (qtd_pontos, ultimo_mes)} das séries que foram atualizadas."""
    hoje = hoje or datetime.date.today()
    inicio = _inicio_da_janela(hoje, MESES_HISTORICO)
    existentes = tr.ler(caminho)
    por_serie = {s["codigo"]: [r for r in existentes if r["codigo"] == s["codigo"]] for s in tr.SERIES}
    atualizadas = {}
    for s in tr.SERIES:
        try:
            pontos = buscar_serie(s, inicio, hoje, get=get)
        except (requests.RequestException, ValueError) as e:
            print("AVISO taxas BCB: série %d (%s) não atualizada (%s); mantendo o que já existe" % (s["codigo"], s["nome"], e))
            continue
        if len(pontos) < MINIMO_DE_PONTOS:
            print("AVISO taxas BCB: série %d veio com só %d pontos válidos (mínimo %d); mantendo o que já existe" % (s["codigo"], len(pontos), MINIMO_DE_PONTOS))
            continue
        por_serie[s["codigo"]] = [{"codigo": s["codigo"], "modalidade": s["nome"], "mes": m, "valor": v, "unidade": s["unidade"]} for m, v in pontos]
        atualizadas[s["codigo"]] = (len(pontos), pontos[-1][0])
    if atualizadas:
        tr.salvar([r for linhas in por_serie.values() for r in linhas], caminho)
    return atualizadas


if __name__ == "__main__":
    try:
        resultado = atualizar()
    except OSError as e:
        print("AVISO taxas BCB: não consegui gravar o CSV (%s)" % e)
        sys.exit(0)
    for codigo, (n, ultimo) in sorted(resultado.items()):
        print("OK taxas BCB: série %d com %d meses, último %s" % (codigo, n, ultimo))
    if not resultado:
        print("AVISO taxas BCB: nenhuma série atualizada; CSV mantido")
    sys.exit(0)
