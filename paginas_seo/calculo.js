/* GERADO por gerador_homeequity.py a partir de calculo.py e dados/taxas_referencia.csv. Não edite à mão.
   Mesma conta de calculo.py (os testes comparam os dois). */
(function (root) {
  'use strict';
  var TAXA_PARCEIRO_AM = 1.09;
  var LTV_MAX = 0.6;
  var CREDITO_MAX = 3000000;
  var PRAZO_MIN_ANOS = 2;
  var PRAZO_MAX_ANOS = 20;
  var IMOVEL_MIN = 100000;
  var IMOVEL_MAX = 20000000;
  var RECEBER_MIN = 50000;
  var RENDA_REFERENCIA = 0.3;
  // Referências do Banco Central (médias de mercado, não oferta): IPCA em 12 meses e taxa média de crédito com garantia real (% ao mês).
  var REF = {"chequeAm": 7.5316195526967, "chequeMes": "set/2026", "garantiaRealAm": 2.14, "garantiaRealMes": "set/2026", "ipca12m": 4.63, "ipcaMes": "out/2026", "pessoalAm": 6.417547301774995, "pessoalMes": "set/2026", "rotativoAm": 15.294671960948625, "rotativoMes": "set/2026"};

  function ipcaMensal(ipca12m) { return Math.pow(1 + ipca12m / 100, 1 / 12) - 1; }
  function taxaMensal(ipca12m) { return (1 + TAXA_PARCEIRO_AM / 100) * (1 + ipcaMensal(ipca12m)) - 1; }
  function pmt(principal, i, n) { return i === 0 ? principal / n : principal * i / (1 - Math.pow(1 + i, -n)); }
  function valorPresente(parcela, i, n) { return i === 0 ? parcela * n : parcela * (1 - Math.pow(1 + i, -n)) / i; }
  function valorPresenteSac(primeira, i, n) { return primeira / (1 / n + i); }
  function limiteCredito(imovel) { return Math.min(LTV_MAX * imovel, CREDITO_MAX); }
  function rendaParaParcela(parcela, fracao) { return parcela / (fracao === undefined ? RENDA_REFERENCIA : fracao); }

  // [primeira parcela, última parcela, total pago]. No Price as duas parcelas são iguais; no SAC a parcela cai todo mês.
  function plano(credito, i, meses, sistema) {
    if (sistema === 'sac') {
      var am = credito / meses;
      return [am + credito * i, am * (1 + i), credito + credito * i * (meses + 1) / 2];
    }
    var p = pmt(credito, i, meses);
    return [p, p, p * meses];
  }

  function simular(imovel, receber, saldo, meses, i, sistema) {
    var credito = receber + saldo;
    var pl = plano(credito, i, meses, sistema);
    return { credito: credito, parcela: pl[0], parcelaFinal: pl[1], total: pl[2], juros: pl[2] - credito, ltv: imovel > 0 ? credito / imovel : 0,
             limite: limiteCredito(imovel), acimaLimite: credito > limiteCredito(imovel) + 1e-9 };
  }

  function receberParaParcela(parcelaAlvo, saldo, meses, i, passo, sistema) {
    var bruto = (sistema === 'sac' ? valorPresenteSac(parcelaAlvo, i, meses) : valorPresente(parcelaAlvo, i, meses)) - saldo;
    return Math.max(0, Math.floor(bruto / passo) * passo);
  }

  function amortizacaoAnual(credito, i, meses, sistema) {
    var parcela = pmt(credito, i, meses), amSac = credito / meses, saldo = credito, restante = meses, ano = 0, linhas = [];
    while (restante > 0) {
      ano += 1;
      var juros = 0, amortizado = 0, n = Math.min(12, restante);
      for (var k = 0; k < n; k++) { var j = saldo * i, a = sistema === 'sac' ? amSac : parcela - j; saldo -= a; juros += j; amortizado += a; }
      restante -= 12;
      linhas.push({ ano: ano, juros: juros, amortizacao: amortizado, saldo: saldo > 0.005 ? saldo : 0 });
    }
    return linhas;
  }

  // Total pago até o fim de cada mês (índice 0 = 0): a linha do gráfico "quanto você terá pago ao longo do tempo".
  function acumuladoMensal(credito, i, meses, sistema) {
    var saida = [0], total = 0, k;
    if (sistema === 'sac') {
      var am = credito / meses, saldo = credito;
      for (k = 0; k < meses; k++) { total += am + saldo * i; saldo -= am; saida.push(total); }
      return saida;
    }
    var p = pmt(credito, i, meses);
    saida = [];
    for (k = 0; k <= meses; k++) saida.push(p * k);
    return saida;
  }

  function compararQuitacao(divida, taxaDividaAm, meses, i, sistema) {
    var atual = pmt(divida, taxaDividaAm, meses), pl = plano(divida, i, meses, sistema);
    return { divida: divida, parcelaAtual: atual, totalAtual: atual * meses, jurosMes1: divida * taxaDividaAm,
             parcelaHe: pl[0], totalHe: pl[2], economiaMes: atual - pl[0], economiaTotal: atual * meses - pl[2] };
  }

  function brl(v) { return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(Math.round(v)); }
  function pct(v) { return v.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + '%'; }

  var api = { TAXA_PARCEIRO_AM: TAXA_PARCEIRO_AM, LTV_MAX: LTV_MAX, CREDITO_MAX: CREDITO_MAX, PRAZO_MIN_ANOS: PRAZO_MIN_ANOS, PRAZO_MAX_ANOS: PRAZO_MAX_ANOS, IMOVEL_MIN: IMOVEL_MIN, IMOVEL_MAX: IMOVEL_MAX, RECEBER_MIN: RECEBER_MIN, RENDA_REFERENCIA: RENDA_REFERENCIA,
              ref: REF, ipcaMensal: ipcaMensal, taxaMensal: taxaMensal, pmt: pmt, valorPresente: valorPresente, valorPresenteSac: valorPresenteSac, plano: plano, rendaParaParcela: rendaParaParcela, limiteCredito: limiteCredito,
              simular: simular, receberParaParcela: receberParaParcela, amortizacaoAnual: amortizacaoAnual, acumuladoMensal: acumuladoMensal, compararQuitacao: compararQuitacao, brl: brl, pct: pct };
  root.DatalabHomeEquity = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
