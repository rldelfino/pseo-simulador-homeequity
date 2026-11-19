/* Interface do simulador de Home Equity. Só textContent e atributos SVG (nada de innerHTML). Depende de calculo.js (window.DatalabHomeEquity).
   Sem cookies e sem dado pessoal: o simulador não envia nada para fora, só mede o uso (valor a receber e prazo) no Umami, sem identificar ninguém. */
(function () {
  'use strict';
  var H = window.DatalabHomeEquity;
  if (!H) return;

  var estado = { financiado: false, imovel: 800000, saldo: 0, receber: 250000, anos: 15, conforto: 3000, divida: 60000, tipoDiv: 'pessoal', taxaDiv: 5 };
  var usou = false;
  var usouQuitar = false;
  var abriuAmort = false;
  var desenhos = 0;
  var timerUrl = null;
  var timerCopiado = null;
  var BRL_NUM = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 });

  function $(id) { return document.getElementById(id); }
  function clamp(v, a, b) { return Math.min(b, Math.max(a, v)); }
  function limpar(no) { while (no.firstChild) no.removeChild(no.firstChild); }
  function evento(nome, dados) {
    try { if (window.umami && window.umami.track) window.umami.track(nome, dados); } catch (e) { /* medição nunca quebra o simulador */ }
  }
  function el(tag, classe, texto) {
    var e = document.createElement(tag);
    if (classe) e.className = classe;
    if (texto !== undefined) e.textContent = texto;
    return e;
  }
  function mil(v) { return v >= 1000000 ? (v / 1000000).toLocaleString('pt-BR', { maximumFractionDigits: 1 }) + ' milhões' : 'R$ ' + Math.round(v / 1000) + ' mil'; }

  function lerNumero(texto) {
    var t = String(texto).replace(/[^\d.,]/g, '');
    if (t.indexOf(',') >= 0) t = t.replace(/\./g, '').replace(',', '.');
    else if (/\.\d{3}(\.|$)/.test(t)) t = t.replace(/\./g, '');
    var n = Number(t);
    return isFinite(n) ? n : 0;
  }

  function maxReceber() { return Math.max(0, H.limiteCredito(estado.imovel) - estado.saldo); }
  function limiteTeto() { return H.LTV_MAX * estado.imovel > H.CREDITO_MAX; }
  function minReceber() { return Math.min(H.RECEBER_MIN, maxReceber()); }
  function taxa() { return H.taxaMensal(H.ref.ipca12m); }

  // estado.receber é o que a pessoa pediu; rec() é o que vale na conta (dentro do limite). O pedido só muda quando ela mexe no campo.
  function rec() { return clamp(estado.receber, minReceber(), maxReceber()); }

  function ajustar() {
    estado.imovel = clamp(estado.imovel, H.IMOVEL_MIN, H.IMOVEL_MAX);
    if (!estado.financiado) estado.saldo = 0;
    estado.saldo = clamp(estado.saldo, 0, H.limiteCredito(estado.imovel));
    return rec() !== estado.receber;
  }

  function preencherRange(r, valor) {
    var min = Number(r.min), max = Number(r.max);
    var v = clamp(valor, min, max);
    r.value = v;
    // Sem style inline nem CSSOM (a CSP não permite e o Safari reclama): o CSS tem uma regra por inteiro de 0 a 100, escolhida por data-p.
    r.setAttribute('data-p', String(Math.round(max > min ? ((v - min) / (max - min)) * 100 : 0)));
  }

  function cartaoAlt(titulo, parcela, linhas, atual, destaque) {
    var d = el('div', 'alt' + (atual ? ' cur' : ''));
    d.appendChild(el('h3', '', titulo));
    d.appendChild(el('div', 'p num', H.brl(parcela)));
    var info = el('div', 'd');
    linhas.forEach(function (l, i) { if (i) info.appendChild(document.createElement('br')); info.appendChild(document.createTextNode(l)); });
    if (destaque) { info.appendChild(document.createElement('br')); info.appendChild(el('span', destaque.cls, destaque.texto)); }
    d.appendChild(info);
    return d;
  }

  var NS = 'http://www.w3.org/2000/svg';
  var CIRC = 289.0265; // circunferência da rosca (raio 46)
  function svgEl(tag, atributos) {
    var e = document.createElementNS(NS, tag);
    Object.keys(atributos).forEach(function (k) { e.setAttribute(k, String(atributos[k])); });
    return e;
  }

  // Rosca: do total pago, quanto é crédito e quanto é juros.
  function desenharRosca(r, semMargem) {
    var pj = !semMargem && r.total > 0 ? r.juros / r.total : 0;
    $('rosca-cred').setAttribute('stroke-dasharray', (semMargem ? 0 : (1 - pj) * CIRC).toFixed(1) + ' ' + CIRC.toFixed(2));
    $('rosca-pct').textContent = semMargem ? '—' : Math.round(pj * 100) + '%';
    $('rosca-cred-v').textContent = semMargem ? '—' : H.brl(r.credito);
    $('rosca-juros-v').textContent = semMargem ? '—' : H.brl(r.juros);
    $('rosca-svg').setAttribute('aria-label', semMargem ? 'Sem simulação' : 'Do total pago, ' + Math.round(pj * 100) + '% é juros');
  }

  // Gráfico anual: barras (juros em cima, amortização embaixo) e linha do saldo devedor.
  function desenharGrafAmort(linhas, credito, parcelaAno) {
    var g = $('amort-graf');
    limpar(g);
    var n = linhas.length, W = 640, Hh = 220, topo = 12, base = Hh - 4, util = base - topo;
    var slot = W / n, larg = Math.max(4, slot * 0.68);
    var pontos = ['0,' + (base - util).toFixed(1)];
    linhas.forEach(function (x, k) {
      var x0 = k * slot + (slot - larg) / 2;
      var hA = (x.amortizacao / parcelaAno) * util, hJ = (x.juros / parcelaAno) * util;
      g.appendChild(svgEl('rect', { 'class': 'g-a', x: x0.toFixed(1), y: (base - hA).toFixed(1), width: larg.toFixed(1), height: Math.max(0, hA).toFixed(1) }));
      g.appendChild(svgEl('rect', { 'class': 'g-j', x: x0.toFixed(1), y: (base - hA - hJ).toFixed(1), width: larg.toFixed(1), height: Math.max(0, hJ).toFixed(1) }));
      pontos.push(((k + 1) * slot).toFixed(1) + ',' + (base - (x.saldo / credito) * util).toFixed(1));
    });
    g.appendChild(svgEl('polyline', { 'class': 'g-s', points: pontos.join(' ') }));
    $('amort-ano-fim').textContent = 'Ano ' + n;
    g.setAttribute('aria-label', 'Gráfico: no ano 1, ' + H.brl(linhas[0].juros) + ' de juros e ' + H.brl(linhas[0].amortizacao) + ' de amortização; no ano ' + n + ', ' +
      H.brl(linhas[n - 1].juros) + ' de juros e ' + H.brl(linhas[n - 1].amortizacao) + ' de amortização. O saldo devedor cai até zero.');
  }

  function desenharRaio(r, i, meses) {
    var c = estado.conforto;
    var txt;
    if (c > 0) {
      var dif = r.parcela - c;
      txt = dif > 0
        ? 'Com a estimativa de ' + H.brl(r.parcela) + ', este cenário fica ' + H.brl(dif) + ' acima do valor que você informou. Veja o que muda com a mesma taxa:'
        : 'Com a estimativa de ' + H.brl(r.parcela) + ', este cenário cabe no valor que você informou (' + H.brl(-dif) + ' abaixo). Veja o que muda com a mesma taxa:';
    } else {
      txt = 'Com a estimativa de ' + H.brl(r.parcela) + ', veja o que muda com a mesma taxa. Informe uma parcela confortável para comparar com o seu orçamento.';
    }
    $('raio-texto').textContent = txt;

    var alvo = $('alts');
    limpar(alvo);
    alvo.appendChild(cartaoAlt('Seu cenário', r.parcela, ['Receber ' + H.brl(rec()) + ' em ' + estado.anos + ' anos', 'Total: ' + H.brl(r.total)], true));

    // receber menos (nunca abaixo do mínimo da ferramenta; se não dá para ir abaixo, mostra "receber mais"; se nem isso, só o outro prazo)
    var menos;
    var cabe = false;
    if (c > 0 && r.parcela > c) {
      menos = H.receberParaParcela(c, estado.saldo, meses, i, 5000);
      cabe = menos >= minReceber();
    }
    if (!cabe) menos = Math.floor((rec() * 0.8) / 5000) * 5000;
    if (menos >= rec()) menos = rec() - 5000;
    if (menos >= minReceber()) {
      var r2 = H.simular(estado.imovel, menos, estado.saldo, meses, i);
      var nota = (c > 0 && r2.parcela <= c * 1.005) ? { cls: 'dn', texto: 'cabe na parcela que você informou' }
        : (c > 0 && r.parcela > c) ? { cls: 'dn', texto: 'fica mais perto do que você informou' } : { cls: 'dn', texto: 'parcela menor, mesmo prazo' };
      alvo.appendChild(cartaoAlt('Receber menos: ' + H.brl(menos), r2.parcela, ['Total: ' + H.brl(r2.total)], false, nota));
    } else {
      var mais = Math.min(Math.floor(maxReceber() / 5000) * 5000, Math.ceil((rec() * 1.2) / 5000) * 5000);
      if (mais > rec()) {
        var r4 = H.simular(estado.imovel, mais, estado.saldo, meses, i);
        alvo.appendChild(cartaoAlt('Receber mais: ' + H.brl(mais), r4.parcela, ['Total: ' + H.brl(r4.total)], false, { cls: 'up', texto: 'parcela maior, mesmo prazo' }));
      }
    }

    // prazo diferente
    var longo = estado.anos < 20;
    var anos3 = longo ? 20 : 10;
    var r3 = H.simular(estado.imovel, rec(), estado.saldo, anos3 * 12, i);
    alvo.appendChild(cartaoAlt((longo ? 'Prazo maior: ' : 'Prazo menor: ') + anos3 + ' anos', r3.parcela, ['Total: ' + H.brl(r3.total)], false,
      longo ? { cls: 'up', texto: 'parcela menor, mais juros no total' } : { cls: 'up', texto: 'parcela maior, menos juros no total' }));
    alvo.className = 'alts' + (alvo.children.length === 2 ? ' dois' : '');
  }

  function desenharNota(i, meses) {
    var mercado = H.ref.garantiaRealAm / 100;
    var r = H.simular(estado.imovel, rec(), estado.saldo, meses, mercado);
    $('nota-taxa-texto').textContent = 'A estimativa usa a taxa de referência do parceiro (' + H.pct(H.TAXA_PARCEIRO_AM) + ' a.m. + IPCA, cerca de ' + H.pct(i * 100) +
      ' a.m.). A média do Banco Central para crédito com garantia real é ' + H.pct(H.ref.garantiaRealAm) + ' a.m. (' + H.ref.garantiaRealMes +
      '): nessa taxa, a parcela do cenário acima seria de ' + H.brl(r.parcela) + '. A taxa final vem da análise.';
  }

  function celula(tag, texto, escopo) {
    var c = el(tag, '', texto);
    if (escopo) c.setAttribute('scope', escopo);
    return c;
  }

  // Amortização ano a ano (mesma conta de calculo.py: amortizacao_anual). Texto igual ao de conteudo.py.
  function desenharAmort(r, i, meses, semMargem) {
    var corpo = $('amort-corpo'), rodape = $('amort-rodape');
    limpar(corpo); limpar(rodape);
    if (semMargem) {
      $('amort-resumo').textContent = 'Ajuste o saldo ou o valor do imóvel para ver a amortização.';
      $('amort-nota').textContent = '';
      $('amort-pct').textContent = '—';
      limpar($('amort-graf'));
      return;
    }
    var linhas = H.amortizacaoAnual(r.credito, i, meses);
    var pago = r.parcela * 12;
    var j1 = linhas[0].juros;
    $('amort-pct').textContent = Math.round((j1 / pago) * 100) + '%';
    desenharGrafAmort(linhas, r.credito, pago);
    $('amort-resumo').textContent = 'No primeiro ano, ' + H.brl(j1) + ' dos ' + H.brl(pago) + ' que você paga são juros (' + Math.round((j1 / pago) * 100) +
      '%). A parcela é fixa: com o tempo ela amortiza mais a dívida e os juros caem.';
    var juros = 0;
    linhas.forEach(function (x) {
      var tr = el('tr');
      tr.appendChild(celula('th', String(x.ano), 'row'));
      tr.appendChild(celula('td', H.brl(x.juros)));
      tr.appendChild(celula('td', H.brl(x.amortizacao)));
      tr.appendChild(celula('td', H.brl(x.saldo)));
      corpo.appendChild(tr);
      juros += x.juros;
    });
    var t = el('tr');
    t.appendChild(celula('th', 'Total', 'row'));
    t.appendChild(celula('td', H.brl(juros)));
    t.appendChild(celula('td', H.brl(r.credito)));
    t.appendChild(celula('td', ''));
    rodape.appendChild(t);
    $('amort-nota').textContent = 'A conta mantém o IPCA em ' + H.pct(H.ref.ipca12m) + ' ao ano (últimos 12 meses, ' + H.ref.ipcaMes +
      ') e a parcela fixa. Se o IPCA mudar, a parcela e o saldo mudam. Não inclui IOF, avaliação do imóvel, registro nem seguros.';
  }

  // "Quitar dívida cara": a mesma dívida e o mesmo prazo na taxa média da dívida e no Home Equity (conteudo.py: quitar_cartoes/quitar_texto).
  function taxaDivida() { return estado.tipoDiv === 'outra' ? estado.taxaDiv : H.ref[estado.tipoDiv + 'Am']; }

  // Barras lado a lado: parcela por mês e total pago, dívida atual x Home Equity.
  function grupoBarras(titulo, valA, valB, nomeA) {
    var g = el('div', 'qg');
    g.appendChild(el('h4', '', titulo));
    var max = Math.max(valA, valB, 1);
    [[nomeA, valA, '#64748b'], ['Home Equity', valB, '#4aa3b5']].forEach(function (b) {
      var linha = el('div', 'r');
      linha.appendChild(el('span', '', b[0]));
      var s = svgEl('svg', { width: '100%', height: 12, role: 'img', 'aria-label': titulo + ', ' + b[0] + ': ' + H.brl(b[1]) });
      s.appendChild(svgEl('rect', { width: '100%', height: 12, rx: 6, fill: 'rgba(255,255,255,.07)' }));
      s.appendChild(svgEl('rect', { width: Math.max(1.5, (b[1] / max) * 100).toFixed(1) + '%', height: 12, rx: 6, fill: b[2] }));
      linha.appendChild(s);
      linha.appendChild(el('span', 'vv num', H.brl(b[1])));
      g.appendChild(linha);
    });
    return g;
  }

  function desenharGrafQuitar(c, nomeA) {
    var alvo = $('q-grafico');
    limpar(alvo);
    alvo.appendChild(grupoBarras('Parcela por mês', c.parcelaAtual, c.parcelaHe, nomeA));
    alvo.appendChild(grupoBarras('Total pago em ' + estado.anos + ' anos', c.totalAtual, c.totalHe, nomeA));
  }

  function desenharQuitar(i, meses, rmax) {
    var outra = estado.tipoDiv === 'outra';
    var t = taxaDivida();
    var d = estado.divida;
    var aviso = $('q-aviso'), cartoes = $('q-cartoes'), texto = $('q-texto'), usar = $('btn-usar-divida');
    $('bloco-taxa-div').hidden = !outra;
    var erro = '';
    if (!(d > 0)) erro = 'Informe quanto você deve.';
    else if (outra && !(t >= 0.1 && t <= 30)) erro = 'Informe uma taxa entre 0,1% e 30% ao mês.';
    else if (rmax < 1) erro = 'O saldo devedor do imóvel já usa o limite: não sobra valor para quitar outra dívida.';
    if (erro) {
      aviso.hidden = false; aviso.textContent = erro;
      limpar(cartoes); limpar($('q-grafico')); texto.textContent = ''; usar.disabled = true;
      return;
    }
    usar.disabled = false;
    var uso = Math.min(d, rmax);
    var msg = '';
    if (d > rmax) msg = 'O limite do imóvel cobre até ' + H.brl(rmax) + ': calculamos com esse valor.';
    else if (d < H.RECEBER_MIN) msg = 'Como referência de mercado, o Home Equity costuma ter crédito mínimo de ' + H.brl(H.RECEBER_MIN) + ': abaixo disso a troca pode não estar disponível.';
    aviso.hidden = !msg; aviso.textContent = msg;
    var c = H.compararQuitacao(uso, t / 100, meses, i);
    limpar(cartoes);
    cartoes.appendChild(cartaoAlt((outra ? 'Na taxa da sua dívida (' : 'Na taxa média (') + H.pct(t) + ' a.m.)', c.parcelaAtual,
      ['Só de juros: ' + H.brl(c.jurosMes1) + ' no 1º mês', 'Total em ' + estado.anos + ' anos: ' + H.brl(c.totalAtual)], false));
    var dest = c.economiaMes > 0 ? { cls: 'dn', texto: H.brl(c.economiaMes) + ' a menos por mês' } : { cls: 'up', texto: 'sem redução de parcela nesta conta' };
    cartoes.appendChild(cartaoAlt('No Home Equity (' + H.pct(i * 100) + ' a.m.)', c.parcelaHe, ['Total em ' + estado.anos + ' anos: ' + H.brl(c.totalHe)], true, dest));
    desenharGrafQuitar(c, outra ? 'Sua dívida' : 'Dívida (média)');
    texto.textContent = c.economiaMes > 0
      ? 'Trocar esta dívida reduziria a parcela em ' + H.brl(c.economiaMes) + ' por mês e o total pago em cerca de ' + H.brl(c.economiaTotal) + ', com a mesma duração (' + estado.anos +
        ' anos). Avaliação, registro e seguros não entram na conta e reduzem essa economia.'
      : 'Com esta taxa, o Home Equity não reduz a parcela da dívida. Peça o CET da proposta e compare antes de decidir.';
  }

  // Endereço compartilhável: só números. O canonical da página continua sendo a home.
  function lerEndereco() {
    try {
      var q = new URLSearchParams(window.location.search);
      var so = /^[\d.,]+$/;
      function num(nome) { var t = q.get(nome) || ''; return so.test(t) ? lerNumero(t) : 0; }
      if (num('imovel') > 0) estado.imovel = num('imovel');
      if (num('saldo') > 0) { estado.saldo = num('saldo'); estado.financiado = true; }
      if (num('receber') > 0) estado.receber = num('receber');
      var a = Math.round(num('prazo'));
      if (a >= H.PRAZO_MIN_ANOS && a <= H.PRAZO_MAX_ANOS) estado.anos = a;
      if (q.get('conforto') !== null) estado.conforto = num('conforto');
    } catch (e) { /* endereço estranho: usa os valores padrão */ }
  }

  // O link compartilhado leva o '#simulador' (abre já no simulador); a barra de endereços fica sem ele,
  // senão o Safari volta para o topo do simulador, e não para onde a pessoa estava, ao voltar de uma página interna.
  function enderecoDaSimulacao(comAncora) {
    var q = new URLSearchParams();
    q.set('imovel', String(Math.round(estado.imovel)));
    if (estado.financiado && estado.saldo > 0) q.set('saldo', String(Math.round(estado.saldo)));
    q.set('receber', String(Math.round(rec())));
    q.set('prazo', String(estado.anos));
    if (estado.conforto > 0) q.set('conforto', String(Math.round(estado.conforto)));
    return window.location.origin + window.location.pathname + '?' + q.toString() + (comAncora ? '#simulador' : '');
  }

  function atualizarEndereco() {
    clearTimeout(timerUrl);
    timerUrl = setTimeout(function () {
      try { window.history.replaceState(null, '', enderecoDaSimulacao(false)); } catch (e) { /* sem histórico: o botão de copiar continua valendo */ }
    }, 400);
  }

  async function copiarLink() {
    var url = enderecoDaSimulacao(true);
    var ok = false;
    try { window.history.replaceState(null, '', enderecoDaSimulacao(false)); } catch (e) { /* ignora */ }
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) { await navigator.clipboard.writeText(url); ok = true; }
    } catch (e) { /* tenta o plano B abaixo */ }
    if (!ok) {
      try {
        var t = document.createElement('textarea');
        t.value = url; t.setAttribute('readonly', ''); t.className = 'sr';
        document.body.appendChild(t); t.select();
        ok = document.execCommand('copy');
        document.body.removeChild(t);
      } catch (e) { ok = false; }
    }
    var msg = $('msg-copiado');
    msg.textContent = ok ? 'Link copiado. Quem abrir vê esta mesma simulação.' : 'Não deu para copiar sozinho. O link já está na barra de endereço do navegador.';
    clearTimeout(timerCopiado);
    timerCopiado = setTimeout(function () { msg.textContent = ''; }, 4000);
    evento('copiou-link', { receber: rec(), prazo: estado.anos });
  }

  function desenhar(foco) {
    var ajustou = ajustar();
    var meses = estado.anos * 12;
    var i = taxa();
    var rmax = maxReceber();
    var semMargem = rmax < 1;
    var r = H.simular(estado.imovel, semMargem ? 0 : rec(), estado.saldo, meses, i);

    $('bloco-saldo').hidden = !estado.financiado;
    $('sit-quitado').checked = !estado.financiado;
    $('sit-financiado').checked = estado.financiado;
    if (foco !== 'imovel') $('campo-imovel').value = BRL_NUM.format(estado.imovel);
    if (foco !== 'saldo') $('campo-saldo').value = BRL_NUM.format(estado.saldo);
    if (foco !== 'receber') $('campo-receber').value = BRL_NUM.format(rec());
    if (foco !== 'conforto') $('campo-conforto').value = estado.conforto > 0 ? BRL_NUM.format(estado.conforto) : '';
    if (foco !== 'prazo') $('campo-prazo').value = String(estado.anos);
    var rp = $('range-prazo');
    rp.min = String(H.PRAZO_MIN_ANOS); rp.max = String(H.PRAZO_MAX_ANOS);
    preencherRange(rp, estado.anos);
    $('div-' + estado.tipoDiv).checked = true;
    if (foco !== 'divida') $('campo-divida').value = BRL_NUM.format(estado.divida);
    if (foco !== 'taxadiv') $('campo-taxa-div').value = String(estado.taxaDiv).replace('.', ',');
    preencherRange($('range-imovel'), estado.imovel);
    var rr = $('range-receber');
    rr.min = String(minReceber()); rr.max = String(Math.max(minReceber(), Math.floor(rmax / 5000) * 5000));
    preencherRange(rr, rec());
    $('min-receber').textContent = mil(Number(rr.min));
    $('max-receber').textContent = mil(Number(rr.max));
    var aviso = $('msg-ajuste');
    if (semMargem) { aviso.hidden = false; aviso.textContent = 'O saldo devedor já usa o limite do imóvel: não sobra valor para receber.'; }
    else if (ajustou && foco !== 'receber' && estado.receber < minReceber()) { aviso.hidden = false; aviso.textContent = 'Ajustamos o valor para o mínimo de ' + H.brl(minReceber()) + '.'; }
    else if (ajustou && foco !== 'receber') { aviso.hidden = false; aviso.textContent = 'Ajustamos o valor para o limite de ' + H.brl(rmax) + (limiteTeto() ? ' (teto de ' + H.brl(H.CREDITO_MAX) + ' de crédito' + (estado.saldo > 0 ? ', menos o saldo' : '') + ').' : ' (60% do imóvel' + (estado.saldo > 0 ? ' menos o saldo' : '') + ').'); }
    else if (!ajustou) aviso.hidden = true;

    $('r-parcela').textContent = semMargem ? '—' : H.brl(r.parcela);
    $('r-sub').textContent = 'em ' + meses + ' meses · taxa de referência ' + H.pct(i * 100) + ' a.m.';
    $('r-total').textContent = semMargem ? '—' : H.brl(r.total);
    $('c-imovel').textContent = H.brl(estado.imovel);
    var usoPct = Math.min(100, r.ltv * 100);
    $('bar-fill').setAttribute('width', usoPct.toFixed(1) + '%');
    $('c-ltv-rot').textContent = estado.financiado ? 'quita o saldo + você recebe' : 'você recebe';
    $('c-credito').textContent = H.brl(r.credito) + ' · ' + Math.round(r.ltv * 100) + '%';
    $('c-limite').textContent = H.brl(r.limite);
    $('c-limite-rot').textContent = limiteTeto() ? 'Limite (teto de crédito)' : 'Limite (60%)';
    $('bar-mark').setAttribute('x', Math.min(99, (r.limite / estado.imovel) * 100).toFixed(1) + '%');
    $('btn-cta').disabled = semMargem;
    desenharRosca(r, semMargem);

    if (!semMargem) { desenharRaio(r, i, meses); } else { limpar($('alts')); $('raio-texto').textContent = 'Ajuste o saldo ou o valor do imóvel para ver as comparações.'; }
    desenharNota(i, meses);
    desenharAmort(r, i, meses, semMargem);
    desenharQuitar(i, meses, rmax);
    desenhos += 1;
    if (desenhos > 1) atualizarEndereco();
  }

  function interagiu() {
    if (usou) return;
    usou = true;
    evento('usou-simulador-homeequity', { receber: rec(), prazo: estado.anos });
  }

  function mexeuQuitar() {
    if (usouQuitar) return;
    usouQuitar = true;
    evento('usou-quitar-divida', { tipo: estado.tipoDiv });
  }

  function ligarCampo(id, chave, minimo, foco, aoMexer) {
    var c = $(id);
    var mexeu = aoMexer || interagiu;
    c.addEventListener('input', function (e) {
      var v = lerNumero(e.target.value);
      if (v >= minimo) { estado[chave] = v; mexeu(); desenhar(foco); }
    });
    c.addEventListener('blur', function (e) {
      estado[chave] = lerNumero(e.target.value);
      if (chave === 'conforto' && e.target.value.trim() === '') estado.conforto = 0;
      mexeu();
      desenhar();
    });
    c.addEventListener('keydown', function (e) { if (e.key === 'Enter') e.target.blur(); });
  }

  // Prazo livre em anos inteiros (de PRAZO_MIN_ANOS a PRAZO_MAX_ANOS): campo de texto e controle deslizante.
  function ligarPrazo() {
    var c = $('campo-prazo'), msg = $('msg-prazo'), min = H.PRAZO_MIN_ANOS, max = H.PRAZO_MAX_ANOS;
    c.addEventListener('input', function (e) {
      var v = Math.round(lerNumero(e.target.value));
      if (v >= min && v <= max) { estado.anos = v; msg.hidden = true; interagiu(); desenhar('prazo'); }
    });
    c.addEventListener('blur', function (e) {
      var v = Math.round(lerNumero(e.target.value));
      if (v >= min && v <= max) msg.hidden = true;
      else {
        v = clamp(v > 0 ? v : estado.anos, min, max);
        msg.hidden = false; msg.textContent = 'O prazo vai de ' + min + ' a ' + max + ' anos. Ajustamos para ' + v + ' anos.';
      }
      estado.anos = v; interagiu(); desenhar();
    });
    c.addEventListener('keydown', function (e) { if (e.key === 'Enter') e.target.blur(); });
    $('range-prazo').addEventListener('input', function (e) { estado.anos = Number(e.target.value); msg.hidden = true; interagiu(); desenhar(); });
  }

  function iniciar() {
    lerEndereco();
    $('sit-quitado').addEventListener('change', function () { estado.financiado = false; estado.saldo = 0; interagiu(); desenhar(); });
    $('sit-financiado').addEventListener('change', function () {
      estado.financiado = true;
      if (estado.saldo === 0) estado.saldo = Math.round(estado.imovel * 0.2 / 10000) * 10000;
      interagiu(); desenhar();
    });
    ligarCampo('campo-imovel', 'imovel', H.IMOVEL_MIN, 'imovel');
    ligarCampo('campo-saldo', 'saldo', 1, 'saldo');
    ligarCampo('campo-receber', 'receber', 1000, 'receber');
    ligarCampo('campo-conforto', 'conforto', 1, 'conforto');
    $('range-imovel').addEventListener('input', function (e) { estado.imovel = Number(e.target.value); interagiu(); desenhar(); });
    $('range-receber').addEventListener('input', function (e) { estado.receber = Number(e.target.value); interagiu(); desenhar(); });
    ligarPrazo();
    $('btn-copiar').addEventListener('click', copiarLink);

    ligarCampo('campo-divida', 'divida', 1, 'divida', mexeuQuitar);
    ligarCampo('campo-taxa-div', 'taxaDiv', 0.01, 'taxadiv', mexeuQuitar);
    Array.prototype.forEach.call(document.querySelectorAll('input[name="tipodiv"]'), function (rd) {
      rd.addEventListener('change', function (e) { estado.tipoDiv = e.target.value; mexeuQuitar(); desenhar(); });
    });
    $('btn-usar-divida').addEventListener('click', function () {
      estado.receber = Math.min(estado.divida, maxReceber());
      interagiu(); desenhar();
      var alvo = $('simulador');
      if (alvo && alvo.scrollIntoView) alvo.scrollIntoView();
    });
    $('det-amort').addEventListener('toggle', function (e) {
      if (e.target.open && !abriuAmort) { abriuAmort = true; evento('abriu-amortizacao', { prazo: estado.anos }); }
    });

    var dlg = $('dlg-confirma');
    function fechar() { if (typeof dlg.close === 'function') dlg.close(); else { dlg.removeAttribute('open'); devolverFoco(); } }
    // Safari não dá foco ao botão no toque: devolvemos o foco para onde a pessoa estava ao fechar a tela.
    function devolverFoco() { try { $('btn-cta').focus({ preventScroll: true }); } catch (e) { /* ignora */ } }
    $('btn-cta').addEventListener('click', function () {
      evento('abriu-confirmacao', { receber: rec(), prazo: estado.anos });
      if (typeof dlg.showModal === 'function') dlg.showModal(); else dlg.setAttribute('open', '');
    });
    dlg.addEventListener('close', devolverFoco);
    $('btn-voltar').addEventListener('click', fechar);
    // Só o clique fora da caixa fecha (o preenchimento interno do diálogo também é o próprio elemento: conferimos pelas coordenadas).
    dlg.addEventListener('click', function (e) {
      if (e.target !== dlg) return;
      var r = dlg.getBoundingClientRect();
      var fora = e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom;
      if (fora) fechar();
    });
    $('a-parceiro').addEventListener('click', function () { evento('cta-parceiro', { receber: rec(), prazo: estado.anos }); });
    desenhar();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar); else iniciar();
})();
