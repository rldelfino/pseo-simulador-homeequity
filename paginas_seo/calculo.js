/* GERADO por gerador_homeequity.py a partir de calculo.py e dados/taxas_referencia.csv. Não edite à mão.
   Mesma conta de calculo.py (os testes comparam os dois). */
(function (root) {
  'use strict';
  var TAXA_PARCEIRO_AM = 1.09;
  var LTV_MAX = 0.6;
  var CREDITO_MAX = 3000000;
  var PRAZOS_ANOS = [5, 8, 10, 12, 15, 18, 20];
  var IMOVEL_MIN = 100000;
  var IMOVEL_MAX = 20000000;
  var RECEBER_MIN = 50000;
  // Referências do Banco Central (médias de mercado, não oferta): IPCA em 12 meses e taxa média de crédito com garantia real (% ao mês).
  var REF = {"chequeAm": 7.5316195526967, "chequeMes": "set/2026", "garantiaRealAm": 2.14, "garantiaRealMes": "set/2026", "ipca12m": 4.63, "ipcaMes": "out/2026", "pessoalAm": 6.417547301774995, "pessoalMes": "set/2026", "rotativoAm": 15.294671960948625, "rotativoMes": "set/2026"};

  function ipcaMensal(ipca12m) { return Math.pow(1 + ipca12m / 100, 1 / 12) - 1; }
  function taxaMensal(ipca12m) { return (1 + TAXA_PARCEIRO_AM / 100) * (1 + ipcaMensal(ipca12m)) - 1; }
  function pmt(principal, i, n) { return i === 0 ? principal / n : principal * i / (1 - Math.pow(1 + i, -n)); }
  function valorPresente(parcela, i, n) { return i === 0 ? parcela * n : parcela * (1 - Math.pow(1 + i, -n)) / i; }
  function limiteCredito(imovel) { return Math.min(LTV_MAX * imovel, CREDITO_MAX); }

  function simular(imovel, receber, saldo, meses, i) {
    var credito = receber + saldo;
    var parcela = pmt(credito, i, meses);
    var total = parcela * meses;
    return { credito: credito, parcela: parcela, total: total, juros: total - credito, ltv: imovel > 0 ? credito / imovel : 0,
             limite: limiteCredito(imovel), acimaLimite: credito > limiteCredito(imovel) + 1e-9 };
  }

  function receberParaParcela(parcelaAlvo, saldo, meses, i, passo) {
    var bruto = valorPresente(parcelaAlvo, i, meses) - saldo;
    return Math.max(0, Math.floor(bruto / passo) * passo);
  }

  function amortizacaoAnual(credito, i, meses) {
    var parcela = pmt(credito, i, meses), saldo = credito, restante = meses, ano = 0, linhas = [];
    while (restante > 0) {
      ano += 1;
      var juros = 0, amortizado = 0, n = Math.min(12, restante);
      for (var k = 0; k < n; k++) { var j = saldo * i, a = parcela - j; saldo -= a; juros += j; amortizado += a; }
      restante -= 12;
      linhas.push({ ano: ano, juros: juros, amortizacao: amortizado, saldo: saldo > 0.005 ? saldo : 0 });
    }
    return linhas;
  }

  function compararQuitacao(divida, taxaDividaAm, meses, i) {
    var atual = pmt(divida, taxaDividaAm, meses), he = pmt(divida, i, meses);
    return { divida: divida, parcelaAtual: atual, totalAtual: atual * meses, jurosMes1: divida * taxaDividaAm,
             parcelaHe: he, totalHe: he * meses, economiaMes: atual - he, economiaTotal: (atual - he) * meses };
  }

  function brl(v) { return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(Math.round(v)); }
  function pct(v) { return v.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + '%'; }

  var api = { TAXA_PARCEIRO_AM: TAXA_PARCEIRO_AM, LTV_MAX: LTV_MAX, CREDITO_MAX: CREDITO_MAX, PRAZOS_ANOS: PRAZOS_ANOS, IMOVEL_MIN: IMOVEL_MIN, IMOVEL_MAX: IMOVEL_MAX, RECEBER_MIN: RECEBER_MIN,
              ref: REF, ipcaMensal: ipcaMensal, taxaMensal: taxaMensal, pmt: pmt, valorPresente: valorPresente, limiteCredito: limiteCredito,
              simular: simular, receberParaParcela: receberParaParcela, amortizacaoAnual: amortizacaoAnual, compararQuitacao: compararQuitacao, brl: brl, pct: pct };
  root.DatalabHomeEquity = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
