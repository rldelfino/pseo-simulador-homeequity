"""Taxas de referência do Banco Central usadas no simulador de Home Equity.

Fonte: BCB/SGS (api.bcb.gov.br), licença ODbL. São MÉDIAS de mercado das novas operações: não são oferta nem a taxa que alguém receberia.
Conferido em 18/11/2026 no catálogo oficial (dadosabertos.bcb.gov.br) e ao vivo na API:
  - 29976: taxa média MENSAL, crédito pessoal não consignado com garantias reais (mistura imóvel e veículo; o BCB não separa).
  - 20742, 20741, 22022: taxas médias ANUAIS de crédito pessoal não consignado, cheque especial e cartão rotativo.
  - 13522: IPCA acumulado em 12 meses (% a.a.), usado na parte "+ IPCA" da taxa de referência do parceiro.

Os dados ficam em dados/taxas_referencia.csv, atualizado por etl_taxas.py.
"""
import csv
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
CAMINHO_CSV = os.path.join(AQUI, "dados", "taxas_referencia.csv")
CABECALHO = ["codigo_serie", "modalidade", "mes_referencia", "valor", "unidade"]

# unidade: "am" = % ao mês; "aa" = % ao ano (a conversão para mensal é feita aqui, em juros compostos)
SERIES = [
    dict(codigo=29976, chave="garantia-real", nome="Crédito com garantia real", unidade="am", faixa=(0.3, 10.0),
         titulo_bcb="Taxa média mensal de juros das operações de crédito com recursos livres - Pessoas físicas - Crédito pessoal não consignado com garantias reais",
         pagina="29976-taxa-media-mensal-de-juros-das-operacoes-de-credito-com-recursos-livres-pessoas-fisicas-credi"),
    dict(codigo=20742, chave="pessoal", nome="Crédito pessoal sem garantia", unidade="aa", faixa=(10.0, 1500.0),
         titulo_bcb="Taxa média de juros das operações de crédito com recursos livres - Pessoas físicas - Crédito pessoal não consignado",
         pagina="20742-taxa-media-de-juros-das-operacoes-de-credito-com-recursos-livres---pessoas-fisicas---credito-"),
    dict(codigo=20741, chave="cheque-especial", nome="Cheque especial", unidade="aa", faixa=(10.0, 1500.0),
         titulo_bcb="Taxa média de juros das operações de crédito com recursos livres - Pessoas físicas - Cheque especial",
         pagina="20741-taxa-media-de-juros-das-operacoes-de-credito-com-recursos-livres---pessoas-fisicas---cheque-e"),
    dict(codigo=22022, chave="cartao-rotativo", nome="Cartão de crédito rotativo", unidade="aa", faixa=(10.0, 3000.0),
         titulo_bcb="Taxa média de juros das operações de crédito com recursos livres - Pessoas físicas - Cartão de crédito rotativo",
         pagina="22022-taxa-media-de-juros-das-operacoes-de-credito-com-recursos-livres---pessoas-fisicas---cartao-d"),
    dict(codigo=13522, chave="ipca-12m", nome="IPCA acumulado em 12 meses", unidade="aa", faixa=(-5.0, 40.0),
         titulo_bcb="Índice nacional de preços ao consumidor-amplo (IPCA) - em 12 meses", pagina=None),
]
CODIGO_IPCA = 13522
CODIGO_GARANTIA_REAL = 29976
CODIGOS_COMPARACAO = [29976, 20742, 20741, 22022]

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]


def serie_def(codigo):
    return next(s for s in SERIES if s["codigo"] == codigo)


def url_json(codigo):
    return "https://api.bcb.gov.br/dados/serie/bcdata.sgs.%d/dados?formato=json" % codigo


def url_fonte(codigo):
    """Página oficial da série (catálogo de dados abertos do BCB) ou, sem página no catálogo, o JSON da API."""
    pagina = serie_def(codigo)["pagina"]
    return "https://dadosabertos.bcb.gov.br/dataset/" + pagina if pagina else url_json(codigo)


def ler(caminho=CAMINHO_CSV):
    """Lista de dicts {codigo, modalidade, mes, valor, unidade}, ordenada por série e mês. Arquivo ausente -> lista vazia."""
    try:
        with open(caminho, encoding="utf-8", newline="") as f:
            linhas = [{"codigo": int(r["codigo_serie"]), "modalidade": r["modalidade"], "mes": r["mes_referencia"],
                       "valor": float(r["valor"]), "unidade": r["unidade"]} for r in csv.DictReader(f, delimiter=";")]
    except FileNotFoundError:
        return []
    return sorted(linhas, key=lambda r: (r["codigo"], r["mes"]))


def salvar(linhas, caminho=CAMINHO_CSV):
    linhas = sorted(linhas, key=lambda r: (r["codigo"], r["mes"]))
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(CABECALHO)
        for r in linhas:
            w.writerow([r["codigo"], r["modalidade"], r["mes"], "%.2f" % r["valor"], r["unidade"]])


def serie(codigo, linhas=None):
    linhas = ler() if linhas is None else linhas
    return [r for r in linhas if r["codigo"] == codigo]


def ultima(codigo, linhas=None):
    s = serie(codigo, linhas)
    return s[-1] if s else None


def mensal_equivalente(taxa_aa):
    """Taxa ao mês equivalente (juros compostos) a uma taxa ao ano, em %."""
    return ((1 + taxa_aa / 100) ** (1 / 12) - 1) * 100


def ao_mes(registro):
    """Valor do registro em % ao mês, qualquer que seja a unidade da série."""
    return registro["valor"] if registro["unidade"] == "am" else mensal_equivalente(registro["valor"])


def mes_extenso(ano_mes):
    ano, mes = ano_mes.split("-")
    return MESES[int(mes) - 1] + " de " + ano
