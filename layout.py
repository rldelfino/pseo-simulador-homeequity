"""HTML do layout (cabeçalho, rodapé), da home e dos blocos dos guias. Os marcadores @@NOME@@ são trocados pelo gerador.

Sem atributo style nem script inline (a CSP não permite). Os desenhos de barras são SVG com atributos; a lógica fica em src/simulador.js.
"""

LOGO = """<span class="tile"><svg viewBox="0 0 44 44" width="32" height="32" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><ellipse cx="22" cy="29" rx="19" ry="6.2" transform="rotate(-22 22 29)" stroke-width="1.3" opacity=".6"/><path d="M17.5 11.5h9M18.8 11.5V22L9.7 37.6a2.3 2.3 0 0 0 2 3.4h20.6a2.3 2.3 0 0 0 2-3.4L25.2 22V11.5" stroke-width="2"/><g fill="currentColor" stroke="none"><rect x="16" y="34" width="2.2" height="4.6" rx=".6"/><rect x="19.6" y="31" width="2.2" height="7.6" rx=".6"/><rect x="23.2" y="33" width="2.2" height="5.6" rx=".6"/><rect x="26.8" y="29.5" width="2.2" height="9.1" rx=".6"/><rect x="19.4" y="6.6" width="1.7" height="3.4" rx=".5"/><rect x="22.4" y="5" width="1.7" height="5" rx=".5"/><rect x="25.4" y="3.6" width="1.7" height="6.4" rx=".5"/><circle cx="31" cy="9.5" r="1.3"/><circle cx="35.5" cy="5.6" r="1.3"/></g><path d="M31 9.5l4.5-3.9" stroke-width="1.3"/></svg></span>"""

LAYOUT = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>@@TITLE@@</title>
<meta name="description" content="@@DESC@@">
<meta name="robots" content="@@ROBOTS@@">
<link rel="canonical" href="@@CANONICAL@@">
<link rel="icon" href="/favicon.ico?v=@@ICONV@@" sizes="any">
<link rel="icon" href="/favicon-32.png?v=@@ICONV@@" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="/apple-touch-icon.png?v=@@ICONV@@">
<meta property="og:type" content="@@OGTYPE@@">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="Datalab Global">
<meta property="og:title" content="@@TITLE@@">
<meta property="og:description" content="@@DESC@@">
<meta property="og:url" content="@@CANONICAL@@">
<meta property="og:image" content="@@DOMINIO@@/og-image.png?v=@@OGV@@">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="@@TITLE@@">
<meta name="twitter:description" content="@@DESC@@">
<meta name="twitter:image" content="@@DOMINIO@@/og-image.png?v=@@OGV@@">
<meta name="theme-color" content="#020617">
<link rel="preload" href="/fonts/playfair-display-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/inter-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/styles.css?v=@@CSSV@@">
<link rel="alternate" type="application/atom+xml" title="Home Equity — Datalab Global" href="/feed.xml">
@@JSONLD@@@@UMAMI@@</head>
<body>
<a href="#conteudo" class="skip">Ir para o conteúdo</a>
<header class="top">
  <div class="wrap">
    <a href="/" class="brand" aria-label="Datalab Global — Home Equity, página inicial">@@LOGO@@<span class="wm"><b>Datalab</b><i>GLOBAL</i></span><span class="prod">Home Equity</span></a>
    <nav class="m" aria-label="Principal">@@NAV@@</nav>
    <div class="free"><span class="dot"></span>Simulação gratuita</div>
    <details class="menu">
      <summary>Menu</summary>
      <nav aria-label="Menu">@@NAVMOBILE@@</nav>
    </details>
  </div>
</header>

<main id="conteudo" class="wrap">
@@MAIN@@
</main>

<footer class="rod">
  <div class="wrap">
    <div class="cols">
      <div>
        <a href="/" class="brand" aria-label="Datalab Global — Home Equity">@@LOGO@@<span class="wm"><b>Datalab</b><i>GLOBAL</i></span></a>
        <p>Simulador de Home Equity: veja parcela e custo total do crédito com imóvel em garantia, antes de qualquer pedido.</p>
      </div>
      <nav aria-label="Entenda"><h2>Entenda</h2><ul>@@FOOT_ENTENDA@@</ul></nav>
      <nav aria-label="Transparência"><h2>Transparência</h2><ul>@@FOOT_TRANSP@@</ul></nav>
      <nav aria-label="Legal"><h2>Legal</h2><ul>@@FOOT_LEGAL@@</ul></nav>
      <nav aria-label="Outros simuladores da Datalab Global"><h2>Outros simuladores</h2><ul>@@FOOT_OUTROS@@</ul></nav>
    </div>
    <div class="base">
      <p>Atualizado em @@ATUALIZADO@@. Taxas de referência: Banco Central e parceiro de crédito.</p>
      <p>Datalab Global é marca de @@RAZAO@@, CNPJ @@CNPJ@@. Contato: <a href="mailto:@@EMAIL@@">@@EMAIL@@</a>.</p>
      <p>A simulação é uma estimativa, não é proposta de crédito. O crédito depende de análise e aprovação, sem garantia de aprovação.</p>
    </div>
  </div>
</footer>
@@SCRIPTS@@</body>
</html>
"""

HOME_MAIN = """  <section class="hero">
    <h1>Quanto o seu imóvel pode <em>liberar?</em></h1>
    <p>Simule a parcela e o custo total do Home Equity em segundos.</p>
    <div class="fine">Grátis · sem cadastro · estimativa, não proposta</div>
  </section>

  <div class="grid" id="simulador">
    <section class="panel" aria-labelledby="t-cenario">
      <h2 id="t-cenario">Seu cenário</h2>
      <div class="f">
        <div class="lb" id="lb-situacao">Situação do imóvel</div>
        <div class="seg" role="radiogroup" aria-labelledby="lb-situacao">
          <input type="radio" name="situacao" id="sit-quitado" value="quitado" checked><label for="sit-quitado">Quitado</label>
          <input type="radio" name="situacao" id="sit-financiado" value="financiado"><label for="sit-financiado">Ainda financiado</label>
        </div>
      </div>
      <div class="f">
        <label for="campo-imovel">Valor do imóvel <span>aproximado</span></label>
        <div class="inp"><span class="pre">R$</span><input id="campo-imovel" type="text" inputmode="numeric" autocomplete="off" value="800.000" class="num"></div>
        <input id="range-imovel" type="range" aria-label="Valor do imóvel, controle deslizante" min="100000" max="5000000" step="10000" value="800000">
        <div class="slabel"><span>R$ 100 mil</span><span>R$ 5 milhões</span></div>
      </div>
      <div class="f" id="bloco-saldo" hidden>
        <label for="campo-saldo">Saldo devedor do financiamento <span>quanto falta pagar</span></label>
        <div class="inp"><span class="pre">R$</span><input id="campo-saldo" type="text" inputmode="numeric" autocomplete="off" value="0" class="num"></div>
        <div class="hint">O novo crédito quita esse saldo e o que sobra vai para você.</div>
      </div>
      <div class="f">
        <label for="campo-receber">Quanto você quer receber <span>valor líquido</span></label>
        <div class="inp"><span class="pre">R$</span><input id="campo-receber" type="text" inputmode="numeric" autocomplete="off" value="250.000" class="num"></div>
        <input id="range-receber" type="range" aria-label="Quanto você quer receber, controle deslizante" min="30000" max="480000" step="5000" value="250000">
        <div class="slabel"><span id="min-receber">R$ 50 mil</span><span id="max-receber">R$ 480 mil</span></div>
        <div class="hint warn" id="msg-ajuste" hidden></div>
      </div>
      <div class="f">
        <label for="campo-prazo">Prazo <span>de @@PRAZO_MIN@@ a @@PRAZO_MAX@@ anos</span></label>
        <div class="inp combo" id="combo-prazo">
          <input id="campo-prazo" type="text" inputmode="numeric" autocomplete="off" value="15" class="num" role="combobox" aria-autocomplete="none" aria-expanded="false" aria-controls="lista-prazo" aria-describedby="msg-prazo" aria-label="Prazo em anos: escolha na lista ou digite">
          <em>anos</em>
          <button type="button" class="caret" id="btn-prazo" aria-label="Abrir a lista de prazos" aria-haspopup="listbox" aria-controls="lista-prazo"><svg viewBox="0 0 12 8" width="12" height="8" aria-hidden="true"><path d="M1 1.5l5 5 5-5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></button>
          <ul class="opts" id="lista-prazo" role="listbox" aria-label="Prazos disponíveis" hidden></ul>
        </div>
        <input id="range-prazo" type="range" aria-label="Prazo em anos, controle deslizante" min="@@PRAZO_MIN@@" max="@@PRAZO_MAX@@" step="1" value="15">
        <div class="slabel"><span>@@PRAZO_MIN@@ anos</span><span>@@PRAZO_MAX@@ anos</span></div>
        <div class="hint warn" id="msg-prazo" hidden></div>
      </div>
    </section>

    <section class="panel resp" id="resultado" aria-labelledby="t-resultado" aria-live="polite">
      <h2 class="sr" id="t-resultado">Resultado da simulação</h2>
      <div class="res">
        <div>
          <div class="kicker" id="r-kicker">Parcela estimada</div>
          <div class="big num"><span id="r-parcela">@@D_PARCELA@@</span> <small>/mês</small></div>
          <div class="dim" id="r-sub">@@D_SUB@@</div>
          <div class="dim ult" id="r-ultima" hidden></div>
          <hr class="sep">
          <div class="dim">Total estimado ao final</div>
          <div class="mid num" id="r-total">@@D_TOTAL@@</div>
          <div class="dim"><a href="/metodologia">Como calculamos</a></div>
        </div>
        <div class="ctx sis">
          <div class="t" id="lb-sistema">Tipo de parcela</div>
          <div class="seg s2" role="radiogroup" aria-labelledby="lb-sistema">
            <input type="radio" name="sistema" id="sis-price" value="price" checked><label for="sis-price">Price <small>parcela fixa</small></label>
            <input type="radio" name="sistema" id="sis-sac" value="sac"><label for="sis-sac">SAC <small>parcela cai</small></label>
          </div>
          <div class="hint" id="hint-sistema">@@D_HINT_SIS@@</div>
        </div>
      </div>
      <div class="rosca">
        <svg viewBox="0 0 120 120" width="120" height="120" role="img" id="rosca-svg" aria-label="Do total pago, @@D_PCT_JUROS@@% é juros">
          <circle cx="60" cy="60" r="46" fill="none" stroke="#cbd5e1" stroke-width="14"/>
          <circle id="rosca-cred" cx="60" cy="60" r="46" fill="none" stroke="#4aa3b5" stroke-width="14" stroke-dasharray="@@D_ROSCA_P@@ 289.03" transform="rotate(-90 60 60)"/>
          <text x="60" y="61" text-anchor="middle" class="rc-n" id="rosca-pct">@@D_PCT_JUROS@@%</text>
          <text x="60" y="77" text-anchor="middle" class="rc-t">em juros</text>
        </svg>
        <div class="rc-l">
          <div class="kicker">Para onde vai o total</div>
          <div class="lg"><span><s></s>Crédito</span><b class="num" id="rosca-cred-v">@@D_L_CRED@@</b></div>
          <div class="lg"><span><s class="jr"></s>Juros</span><b class="num" id="rosca-juros-v">@@D_L_JUROS@@</b></div>
        </div>
      </div>
      <div class="rodape-res">
        <div class="cta">
          <div><strong>Faça sua proposta</strong><span class="s">Com um parceiro de crédito · sem compromisso</span></div>
          <button type="button" class="btn" id="btn-cta">Consultar opções →</button>
        </div>
        <div class="fine2">Estimativa: a taxa final depende da análise. O imóvel fica como garantia da operação — <a href="#garantia">entenda abaixo</a>.</div>
        <div class="copiar"><button type="button" id="btn-copiar">Copiar o link desta simulação</button><span id="msg-copiado" role="status"></span></div>
      </div>
    </section>
  </div>

  <div class="uso" aria-label="Quanto do valor do imóvel o crédito usa">
    <div class="uso-t"><span class="t">Valor do imóvel</span><b class="v num" id="c-imovel">R$ 800.000</b></div>
    <div class="uso-b"><svg class="bar" id="bar-ltv" width="100%" height="12" role="img" aria-label="Quanto do valor do imóvel o crédito usa">
            <rect width="100%" height="12" rx="6" fill="rgba(255,255,255,.1)"/><rect id="bar-fill" width="@@D_BARRA@@%" height="12" rx="6" fill="#4aa3b5"/><rect id="bar-mark" x="60%" y="-3" width="2" height="18" fill="#e2e8f0"/>
          </svg></div>
    <div class="uso-l">
      <div class="lg"><span><s></s>Crédito (<span id="c-ltv-rot">você recebe</span>)</span><b class="num" id="c-credito">@@D_CREDITO@@</b></div>
      <div class="lg"><span><s class="lim"></s><span id="c-limite-rot">Limite (60%)</span></span><b class="num" id="c-limite">@@D_LIMITE@@</b></div>
    </div>
  </div>

  <section class="band fatos" aria-label="Condições divulgadas por um parceiro de crédito">
    <div class="fatos-g">
      <div><b class="num">@@FATO_TAXA@@</b><span>ao mês + IPCA, a partir de</span></div>
      <div><b class="num">@@FATO_LTV@@</b><span>do valor do imóvel, no máximo</span></div>
      <div><b class="num">@@FATO_PRAZO@@</b><span>de prazo, no máximo</span></div>
      <div><b class="num">R$ 0</b><span>e sem cadastro para simular</span></div>
    </div>
    <p class="hint">Condições divulgadas por um parceiro de crédito. A taxa final e o limite saem da análise do pedido.</p>
  </section>

  <section class="blk" aria-labelledby="t-raio">
    <div class="raio">
      <div class="hd">
        <div><div class="kicker">Raio-X da decisão</div><h2 id="t-raio">Essa parcela cabe no seu mês?</h2></div>
      </div>
      <div class="mini-in"><label for="campo-conforto">Parcela confortável: quanto cabe por mês?</label><div class="inp"><span class="pre">R$</span><input id="campo-conforto" type="text" inputmode="numeric" autocomplete="off" value="3.000" class="num"><em>/mês</em></div></div>
      <p id="raio-texto">@@D_RAIO@@</p>
      <div class="alts" id="alts"></div>
      <div class="regra" id="regra-renda">
        <div class="rt"><b>E o limite de 30% da renda?</b> <span id="renda-texto">@@D_RENDA@@</span></div>
        <details class="rdet" id="det-renda">
          <summary>Como a renda entra na análise do Home Equity</summary>
          @@REGRA_RENDA@@
        </details>
      </div>
      <div class="hint">Não dizemos qual é “melhor”: depende do que importa para você. A parcela confortável é só uma conta sua; não é análise de crédito.</div>
    </div>
  </section>

  <section class="blk" aria-labelledby="t-amort">
    <div class="split">
      <div class="split-t">
        <div class="kicker">Amortização</div>
        <h2 id="t-amort">Para onde vai a sua parcela</h2>
        <div class="giga num"><span id="amort-pct">@@D_AMORT_PCT@@%</span><small>do 1º ano é juros</small></div>
        <p class="lead" id="amort-resumo">@@D_AMORT_RESUMO@@</p>
      </div>
      <div class="panel graf">
        <div class="leg">
          <span><s class="jr"></s>Juros do ano</span><span><s></s>Amortização do ano</span><span><s class="ln"></s>Saldo devedor</span>
        </div>
        <svg id="amort-graf" viewBox="0 0 640 220" preserveAspectRatio="none" role="img" aria-label="Gráfico: juros e amortização de cada ano e saldo devedor"></svg>
        <div class="eixo"><span>Ano 1</span><span id="amort-ano-fim">Ano 15</span></div>
      </div>
    </div>
    <details class="amort" id="det-amort">
      <summary>Ver a amortização ano a ano</summary>
      <div class="tw"><table id="tab-amort">
        <caption id="amort-cap">Parcela fixa: juros, amortização e saldo devedor no fim de cada ano</caption>
        <thead><tr><th scope="col">Ano</th><th scope="col">Juros</th><th scope="col">Amortização</th><th scope="col">Saldo devedor</th></tr></thead>
        <tbody id="amort-corpo">@@D_AMORT_LINHAS@@</tbody>
        <tfoot id="amort-rodape">@@D_AMORT_TOTAL@@</tfoot>
      </table></div>
      <div class="hint" id="amort-nota">@@D_AMORT_NOTA@@</div>
    </details>
  </section>

  <section class="blk" aria-labelledby="t-cmp">
    <div class="kicker">Taxas</div>
    <h2 id="t-cmp">Quanto cada tipo de crédito custa por mês</h2>
    <p class="lead">Com garantia, o juro mensal costuma ser bem menor que o de crédito sem garantia.</p>
    <div class="panel">@@COMPARACAO@@</div>
    <div class="note" id="nota-taxa"><b>E se a taxa for maior?</b> <span id="nota-taxa-texto">@@NOTA_TAXA@@</span></div>
  </section>

  <section class="blk" aria-labelledby="t-cmpmod">
    <div class="kicker">Comparativo</div>
    <h2 id="t-cmpmod">O mesmo crédito em outras modalidades</h2>
    <p class="lead" id="cm-lead">@@D_CM_LEAD@@</p>
    <div class="panel cmpx">
      <div class="cmleg"><span><s class="cr"></s>O que você recebe</span><span><s class="jr2"></s>Juros pagos até o fim</span></div>
      <div class="cmrows" id="cm-linhas"></div>
      <div class="cmgap">
        <div class="gv num" id="cm-gap-v">@@D_CM_GAPV@@</div>
        <p id="cm-gap">@@D_CM_GAP@@</p>
      </div>
    </div>
    <div class="hint" id="cm-nota">@@D_CM_NOTA@@</div>
  </section>

  <section class="band" aria-labelledby="t-quitar">
    <div class="kicker">Dívida cara</div>
    <h2 id="t-quitar">Tem uma dívida cara? Veja se vale trocar</h2>
    <p class="lead">A mesma dívida, no mesmo prazo do simulador, na taxa média do mercado e no Home Equity.</p>
    <div class="qgrid">
      <div class="panel quitar">
        <div class="f">
          <div class="lb" id="lb-tipodiv">Tipo de dívida</div>
          <div class="seg s2" role="radiogroup" aria-labelledby="lb-tipodiv">@@DIVIDA_OPCOES@@</div>
        </div>
        <div class="f">
          <label for="campo-divida">Quanto você deve <span>saldo da dívida</span></label>
          <div class="inp"><span class="pre">R$</span><input id="campo-divida" type="text" inputmode="numeric" autocomplete="off" value="60.000" class="num"></div>
        </div>
        <div class="f" id="bloco-taxa-div" hidden>
          <label for="campo-taxa-div">Taxa da sua dívida <span>% ao mês</span></label>
          <div class="inp"><input id="campo-taxa-div" type="text" inputmode="decimal" autocomplete="off" value="5" class="num"><em>% a.m.</em></div>
        </div>
        <div class="row2"><button type="button" class="ghost" id="btn-usar-divida">Simular com este valor</button></div>
      </div>
      <div class="panel qres">
        <div class="hint warn" id="q-aviso" hidden></div>
        <div class="alts dois" id="q-cartoes">@@D_Q_CARTOES@@</div>
        <div class="qviz" id="q-grafico"></div>
        <p class="qtxt" id="q-texto">@@D_Q_TEXTO@@</p>
      </div>
    </div>
    <div class="hint">Conta de comparação: as duas dívidas têm a mesma duração. Cheque especial e rotativo não costumam durar tanto; o ponto é ver quanto o juro pesa por mês. A troca coloca o imóvel como garantia: <a href="/garantia-do-imovel">veja o que muda</a> e <a href="/custos-alem-dos-juros">os custos além dos juros</a>.</div>
  </section>

  <section class="blk" id="garantia" aria-labelledby="t-gar">
    <div class="split gar">
      <div class="split-t">
        <div class="kicker">Garantia</div>
        <h2 id="t-gar">Como funciona a garantia do imóvel</h2>
        <p class="lead">Entender isso antes ajuda a escolher uma parcela que caiba com folga.</p>
        <p class="hint"><a href="/garantia-do-imovel">Leia o guia completo sobre a garantia</a></p>
      </div>
      <div class="lista3">
        <div class="li3"><span class="n" aria-hidden="true">1</span><div><h4>O que muda para você</h4><ul><li>Você continua morando ou usando o imóvel</li><li>A garantia é o que permite juros menores</li></ul></div></div>
        <div class="li3"><span class="n" aria-hidden="true">2</span><div><h4>O que fica registrado</h4><ul><li>O imóvel é dado em garantia à instituição, com registro em cartório</li><li>O registro sai quando a dívida é quitada</li></ul></div></div>
        <div class="li3"><span class="n" aria-hidden="true">3</span><div><h4>Para ficar tranquilo</h4><ul><li>Escolha uma parcela que caiba com folga</li><li>Em atraso prolongado, a instituição pode seguir o que o contrato prevê</li></ul></div></div>
      </div>
    </div>
  </section>

  <section class="band" aria-labelledby="t-pede">
    <div class="kicker">Documentos</div>
    <h2 id="t-pede">O que o parceiro costuma pedir</h2>
    <p class="lead">Cada instituição tem a sua lista. Em geral, para Home Equity:</p>
    <div class="steps">
      <div class="st"><span class="sn" aria-hidden="true">01</span><h4>Sobre você</h4><ul><li>Documento e estado civil</li><li>Comprovante de renda ou extratos</li><li>Cônjuge ou sócios, se entrarem</li></ul></div>
      <div class="st"><span class="sn" aria-hidden="true">02</span><h4>Sobre o imóvel</h4><ul><li>Matrícula atualizada</li><li>Avaliação do imóvel</li><li>Pode ser financiado, comercial ou de terceiros, conforme a instituição</li></ul></div>
      <div class="st"><span class="sn" aria-hidden="true">03</span><h4>Etapas até receber</h4><ul><li>Análise de crédito</li><li>Avaliação e análise jurídica</li><li>Contrato e registro em cartório</li></ul></div>
    </div>
  </section>

  <section class="blk" aria-labelledby="t-guias">
    <h2 id="t-guias">Entenda antes de decidir</h2>
    <div class="cols3">@@CARTOES@@</div>
  </section>

  <section class="blk split faqs" aria-labelledby="t-faq">
    <div class="split-t">
      <div class="kicker">Dúvidas</div>
      <h2 id="t-faq">Perguntas frequentes</h2>
    </div>
    <div class="faq">@@FAQ@@</div>
  </section>

  <dialog id="dlg-confirma" aria-labelledby="dlg-titulo">
    <h3 id="dlg-titulo">Antes de continuar</h3>
    <p>Você vai preencher um formulário de um <b>parceiro de crédito</b>, que analisa o seu pedido. A página dele mostra o nome da empresa.</p>
    <ul>
      <li>Tipo e valor aproximado do imóvel, e o valor que você quer.</li>
      <li>Dados pessoais e de renda, e documentos do imóvel mais adiante.</li>
      <li>O parceiro pode consultar bureaus de crédito, conforme o aviso dele.</li>
      <li>O imóvel fica como garantia da operação: leia as condições com calma.</li>
      <li>Simular aqui não é aprovação e você não é obrigado a contratar.</li>
    </ul>
    <p class="dim">Veja a <a href="/privacidade">política de privacidade</a> e <a href="/metodologia">como calculamos</a>.</p>
    <div class="row"><a class="btn" id="a-parceiro" href="@@PARCEIRO@@" target="_blank" rel="noopener sponsored">Continuar para o parceiro →</a><button type="button" class="ghost" id="btn-voltar">Voltar e ajustar</button></div>
  </dialog>
"""

GUIA_CABECALHO = """<div class="volta"><a class="btn-volta" href="/#simulador" data-volta>← Voltar à simulação</a></div>
<nav class="crumb" aria-label="Você está em"><a href="/">Home Equity <span>@@ROTULO_PAGINA@@</span></a></nav>
<article class="guia">
  <h1>@@H1@@</h1>
  <p class="meta">Atualizado em @@ATUALIZADO@@ · @@RAZAO@@</p>
  <div class="prose">
"""

GUIA_MEIO = """  </div>
"""

GUIA_FECHO = """  <aside class="fecho">
    <p class="t">Simule com o seu imóvel</p>
    <p>Veja parcela e custo total antes de decidir.</p>
    <a class="btn" href="/#simulador" data-volta>Voltar à simulação →</a>
  </aside>
  <section class="rel" aria-labelledby="veja-tambem">
    <h2 id="veja-tambem">Veja também</h2>
    <ul>@@RELACIONADOS@@</ul>
  </section>
"""
