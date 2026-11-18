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
        <label for="sel-prazo">Prazo <span>até 20 anos</span></label>
        <div class="inp sel"><select id="sel-prazo">@@PRAZOS@@</select></div>
      </div>
    </section>

    <section class="panel" id="resultado" aria-labelledby="t-resultado" aria-live="polite">
      <h2 class="sr" id="t-resultado">Resultado da simulação</h2>
      <div class="res">
        <div>
          <div class="kicker">Parcela estimada</div>
          <div class="big num"><span id="r-parcela">@@D_PARCELA@@</span> <small>/mês</small></div>
          <div class="dim" id="r-sub">@@D_SUB@@</div>
          <hr class="sep">
          <div class="dim">Total estimado ao final</div>
          <div class="mid num" id="r-total">@@D_TOTAL@@</div>
          <div class="dim"><a href="/metodologia">Como calculamos</a></div>
        </div>
        <div class="ctx">
          <div class="t">Valor do imóvel</div>
          <div class="v num" id="c-imovel">R$ 800.000</div>
          <svg class="bar" id="bar-ltv" width="100%" height="12" role="img" aria-label="Quanto do valor do imóvel o crédito usa">
            <rect width="100%" height="12" rx="6" fill="rgba(255,255,255,.1)"/><rect id="bar-fill" width="@@D_BARRA@@%" height="12" rx="6" fill="#4aa3b5"/><rect id="bar-mark" x="60%" y="-3" width="2" height="18" fill="#e2e8f0"/>
          </svg>
          <div class="lg"><span><s></s>Crédito (<span id="c-ltv-rot">você recebe</span>)</span><b class="num" id="c-credito">@@D_CREDITO@@</b></div>
          <div class="lg"><span><s class="lim"></s><span id="c-limite-rot">Limite (60%)</span></span><b class="num" id="c-limite">@@D_LIMITE@@</b></div>
        </div>
      </div>
      <div class="cta">
        <div><strong>Faça sua proposta</strong><span class="s">Com um parceiro de crédito · sem compromisso</span></div>
        <button type="button" class="btn" id="btn-cta">Consultar opções →</button>
      </div>
      <div class="fine2">Estimativa: a taxa final depende da análise. O imóvel fica como garantia da operação — <a href="#garantia">entenda abaixo</a>.</div>
      <div class="copiar"><button type="button" id="btn-copiar">Copiar o link desta simulação</button><span id="msg-copiado" role="status"></span></div>
    </section>
  </div>

  <section class="blk" aria-labelledby="t-raio">
    <div class="raio">
      <div class="hd">
        <div><div class="kicker">Raio-X da decisão</div><h2 id="t-raio">Essa parcela cabe no seu mês?</h2></div>
      </div>
      <div class="mini-in"><label for="campo-conforto">Parcela confortável: quanto cabe por mês?</label><div class="inp"><span class="pre">R$</span><input id="campo-conforto" type="text" inputmode="numeric" autocomplete="off" value="3.000" class="num"><em>/mês</em></div></div>
      <p id="raio-texto">@@D_RAIO@@</p>
      <div class="alts" id="alts"></div>
      <div class="hint">Não dizemos qual é “melhor”: depende do que importa para você. A parcela confortável é só uma conta sua; não é análise de crédito.</div>
    </div>
  </section>

  <section class="blk" aria-labelledby="t-cmp">
    <h2 id="t-cmp">Quanto cada tipo de crédito custa por mês</h2>
    <p class="lead">Com garantia, o juro mensal costuma ser bem menor que o de crédito sem garantia.</p>
    <div class="panel">@@COMPARACAO@@</div>
    <div class="note" id="nota-taxa"><b>E se a taxa for maior?</b> <span id="nota-taxa-texto">@@NOTA_TAXA@@</span></div>
  </section>

  <section class="blk" id="garantia" aria-labelledby="t-gar">
    <h2 id="t-gar">Como funciona a garantia do imóvel</h2>
    <p class="lead">Entender isso antes ajuda a escolher uma parcela que caiba com folga.</p>
    <div class="cols3">
      <div class="card"><h4>O que muda para você</h4><ul><li>Você continua morando ou usando o imóvel</li><li>A garantia é o que permite juros menores</li></ul></div>
      <div class="card"><h4>O que fica registrado</h4><ul><li>O imóvel é dado em garantia à instituição, com registro em cartório</li><li>O registro sai quando a dívida é quitada</li></ul></div>
      <div class="card"><h4>Para ficar tranquilo</h4><ul><li>Escolha uma parcela que caiba com folga</li><li>Em atraso prolongado, a instituição pode seguir o que o contrato prevê</li></ul></div>
    </div>
    <p class="hint"><a href="/garantia-do-imovel">Leia o guia completo sobre a garantia</a></p>
  </section>

  <section class="blk" aria-labelledby="t-pede">
    <h2 id="t-pede">O que o parceiro costuma pedir</h2>
    <p class="lead">Cada instituição tem a sua lista. Em geral, para Home Equity:</p>
    <div class="cols3">
      <div class="card"><h4>Sobre você</h4><ul><li>Documento e estado civil</li><li>Comprovante de renda ou extratos</li><li>Cônjuge ou sócios, se entrarem</li></ul></div>
      <div class="card"><h4>Sobre o imóvel</h4><ul><li>Matrícula atualizada</li><li>Avaliação do imóvel</li><li>Pode ser financiado, comercial ou de terceiros, conforme a instituição</li></ul></div>
      <div class="card"><h4>Etapas até receber</h4><ul><li>Análise de crédito</li><li>Avaliação e análise jurídica</li><li>Contrato e registro em cartório</li></ul></div>
    </div>
  </section>

  <section class="blk" aria-labelledby="t-guias">
    <h2 id="t-guias">Entenda antes de decidir</h2>
    <div class="cols3">@@CARTOES@@</div>
  </section>

  <section class="blk" aria-labelledby="t-faq">
    <h2 id="t-faq">Perguntas frequentes</h2>
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

GUIA_CABECALHO = """<nav class="crumb" aria-label="Você está em"><a href="/">Home Equity <span>@@ROTULO_PAGINA@@</span></a></nav>
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
    <a class="btn" href="/#simulador">Abrir o simulador →</a>
  </aside>
  <section class="rel" aria-labelledby="veja-tambem">
    <h2 id="veja-tambem">Veja também</h2>
    <ul>@@RELACIONADOS@@</ul>
  </section>
"""
