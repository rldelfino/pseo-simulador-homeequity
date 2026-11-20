# Simulador de Home Equity — Datalab Global

Idioma: português do Brasil. Estilo: curto, sem jargão, números reais, dizer o que NÃO foi verificado.
Projeto irmão de `../005-pseo-simulador-emprestimo` (mesmas regras de operação). Plano e desenhos aprovados: `../_plano-equity-condominio/` (PLANO.md, mockups, imagens).

## Regras fixas
- **Graphify primeiro, sem o dono pedir.** Antes de ler arquivo/grep: `graphify update .` e `graphify query "..."`. Se pular, avisar na hora.
- Sem gastar dinheiro. Sem postar nem mandar mensagem a pessoas. Nada de CPF/telefone em log, teste ou arquivo.
- **Mensagem agnóstica sobre o parceiro**: "um parceiro de crédito". Sem texto sobre remuneração/comissão e sem citar o nome do parceiro nem de bancos (há teste que barra). Sem ranking.
- Tom calmo sobre a garantia: aviso curto perto do botão, explicação na seção/página própria. Um valor único de parcela (taxa de referência do parceiro); a média do BCB só na nota "E se a taxa for maior?".
- Link de conversão do parceiro (`LINK_PARCEIRO` em `gerador_homeequity.py`) só no botão da tela de confirmação. Não copiar o link de outros produtos para cá.
- Medição: Umami, **ID próprio deste site** (`UMAMI_ID`, hoje vazio = sem script). Eventos: `usou-simulador-homeequity`, `abriu-confirmacao`, `cta-parceiro`, `copiou-link` (só `receber` e `prazo`), `abriu-amortizacao` (`prazo`), `usou-quitar-divida` (`tipo`: pessoal/cheque/rotativo/outra), `simulou-amortizacao` (`prazo`). Não mandar evento de teste ao Umami (nos testes o Umami é bloqueado).
- Sem segredo em arquivo/GitHub. Sem identificar modelo de IA em commits/PRs (só as linhas de atribuição que o sistema mandar). Python 3.10 no CI (sem f-string aninhado). Merge só com `pytest` saindo 0. Fluxo: branch → PR → merge.
- CSP: sem `style=` nem script inline. Barras são SVG com atributos; preenchimento dos sliders usa `data-p` definido por JS.
- Máximo ~15 páginas indexáveis, cada uma com conteúdo próprio.
- Paleta: azul-petróleo acinzentado `#4aa3b5` (escolhido em 18/11 para não se confundir com o verde do imobiliário e o azul de veículos) (Auto Equity é âmbar, Condomínio terracota; imobiliário verde, veículos azul, Pix roxo).

## Comandos
- Gerar: `python gerador_homeequity.py` (saída em `paginas_seo/`, publicada no Cloudflare Pages sem build). O CSS é escrito à mão em `src/estilo.css` (sem Tailwind/npm).
- Testes: `python -m pytest -q` (108). Amortização e "quitar dívida" no navegador: `python testar_amort_quitar.py` (Chromium + WebKit, desktop e celular).
- Seções da home (18/11): "Para onde vai a sua parcela" (amortização anual recolhível, `calculo.amortizacao_anual`) e "Tem uma dívida cara? Veja se vale trocar" (`calculo.comparar_quitacao`, taxas médias BCB 20742/20741/22022 em `REF`; mesmo prazo do simulador; botão leva o valor ao simulador). Navegador de ponta a ponta (Chromium + WebKit, desktop e celular, 160 checagens no total): `python testar_navegador.py` (precisa do Playwright; fora do CI).
- Ícones e imagem de compartilhamento: `python gerar_icones.py` (Playwright + Pillow).
- Taxas do BCB: `python etl_taxas.py` (grava `dados/taxas_referencia.csv`; falha de rede não derruba). Robô semanal em `.github/workflows/atualiza_taxas.yml` (seg 08:00 UTC): taxas, rebuild, pytest, commit, IndexNow.
- Fontes: `conteudo.py` (textos, títulos ≤ 60), `layout.py` (HTML), `src/simulador.js`, `calculo.py` (conta de referência; `calculo.js` é gerado e os testes comparam as duas via Node).

## Fatos do produto (conferidos em 18/11/2026)
- Parceiro divulga: Home Equity a partir de 1,12% a.m. + IPCA, libera até 60% do valor do imóvel, prazo até 20 anos. Taxa de referência = (1+1,12%)·(1+IPCA mensal)−1, IPCA = série SGS 13522 (12 meses) mantido constante: hoje ≈ 1,47% a.m. Parcela fixa (Price) sobre crédito = receber + saldo devedor (financiado). Não inclui IOF, avaliação, registro, seguros.
- Séries BCB: 29976 (garantia real, a.m., mistura imóvel e veículo), 20742/20741/22022 (a.a.), 13522 (IPCA 12m). Fonte e mês aparecem em `/taxas-de-referencia`.
- Cenário padrão da home: imóvel R$ 800.000, receber R$ 250.000, 15 anos → R$ 3.966/mês, total R$ 713.837 (igual ao desenho aprovado).
- Páginas: home + dados-abertos (CSV das taxas, ODbL, Dataset em JSON-LD), como-funciona, garantia-do-imovel, custos-alem-dos-juros, home-equity-ou-outro-credito, quando-nao-vale-a-pena, taxas-de-referencia, metodologia, sobre, atualizacoes, privacidade, termos (13 no sitemap). Dados: `/dados/taxas-referencia.csv`. Dados abertos só em `/dados-abertos` (sem Kaggle por enquanto).
- Domínio previsto: https://homeequity.datalabglobal.com. IndexNow: chave em `indexnow.py`.

## Estado (18/11/2026)
- Construído, testado e **publicado**: repo `rldelfino/pseo-simulador-homeequity` (main), Cloudflare Pages `pseo-simulador-homeequity` (saída `paginas_seo`, sem build), domínio `homeequity.datalabglobal.com` (CNAME criado pelo Cloudflare). CI verde (62 testes).
- Cloudflare Pages só publica pushes se o app "Cloudflare Workers and Pages" do GitHub tiver acesso ao repositório (Settings > Applications > Configure > Repository access; é uma lista de repositórios, repo novo precisa ser adicionado).
- Umami: plano gratuito só permite 1 site ("Website limit reached"), então `UMAMI_ID` usa o ID compartilhado dos irmãos; filtrar por hostname `homeequity.datalabglobal.com`.
- NÃO verificado: se o formulário do parceiro aceita pré-preenchimento por endereço (hoje abre limpo); iPhone físico; valores mínimo/máximo de crédito do parceiro (o simulador usa mínimo de R$ 50 mil a receber e teto de R$ 3 milhões de crédito como limites de interface, baseados em condições públicas de outras instituições (Creditas R$ 50 mil a R$ 3 mi; Neon até R$ 3 mi), não regra do parceiro); revisão jurídica dos textos.

- Linkado no hub (cartão PT/EN, rodapé, llms.txt) e no rodapé de 002, 003 e 005. Search Console/Bing/IndexNow feitos; DuckDuckGo não tem sitemap (usa o índice do Bing e o rastreador próprio).
- Auditoria e benchmark (18/11): `../_plano-equity-condominio/AUDITORIA-HOME-EQUITY.md`. Conta bate com exemplo público da Creditas (R$ 150 mil, 48 m, IPCA 4,22% → R$ 4.349 / R$ 208,7 mil). Corrigidos: `#simulador` na barra de endereço (Safari voltava ao topo do simulador) e tabelas viram cartões no celular (`data-l` + CSS).

- v2 da home (18/11, feedback do dono): prazo livre de 2 a 20 anos (campo + controle deslizante, `PRAZO_MIN_ANOS`/`PRAZO_MAX_ANOS`; o mínimo de 2 anos é limite da interface, não do parceiro); sem `<select>` (tipo de dívida virou botões); painel do resultado com a mesma altura do cenário e rosca (crédito x juros do total); gráficos SVG feitos no JS (barras juros/amortização + linha do saldo; barras parcela e total na troca de dívida); seções com ritmo variado (faixas de largura total `.band`, números grandes, divisão em duas colunas, passos numerados). Gráficos usam classes CSS (`.g-a`, `.g-j`, `.g-s`), nunca `style`.

- v3 da home (19/11, feedback do dono): (1) botão "Voltar à simulação" fixo no topo das páginas internas e no fecho (`data-volta`, lógica em `src/menu.js`: se veio da home usa `history.back()`, que devolve a rolagem; senão abre a home com a última simulação guardada em `sessionStorage` chave `he-sim`, só nesta aba); (2) prazo = lista suspensa própria (combobox ARIA, 2 a 20 anos) + digitação + controle deslizante, sem `<select>`; (3) Raio-X explica a regra da renda: NÃO há percentual único em lei para Home Equity; 30% (às vezes 35%) é referência de mercado/prática de bancos, o parceiro não divulga o dele (conteudo.regra_renda; `calculo.RENDA_REFERENCIA`); mostra "renda de referência" = parcela/0,30; (4) escolha Price (padrão) ou SAC na mesma taxa (`sistema=sac` no link; SAC mostra 1ª parcela e a última; o parceiro NÃO confirmou quais sistemas oferece: texto diz que ele informa na proposta); (5) barras das outras modalidades com cores leves (`conteudo.COR_MODALIDADE`, mesmas em `simulador.js` `COR`); (6) seção "O mesmo crédito em outras modalidades" (quadro do Home Equity + gráfico de linhas do total pago ao longo do tempo + barras de total e parcela; outras modalidades em parcela fixa, médias BCB).

- v3b (19/11, feedback: "pesado, com muita informação"): o painel do resultado ficou só com parcela, total, escolha Price/SAC (cartão pequeno), rosca e botão; a barra "valor do imóvel/limite" virou uma faixa fina (`.uso`) logo abaixo do simulador (mesmos ids); a renda de referência saiu do painel e fica só no Raio-X. Comparativo redesenhado: 4 linhas (Home Equity, garantia real média, crédito pessoal, cheque especial; rotativo fica de fora, distorce a escala), cada barra = crédito (claro) + juros (cor da modalidade), destaque grande "R$ X a mais no crédito pessoal". Regra de design: o topo da home tem que ser leve; informação extra vai para as seções de baixo.

- SEO (19/11): `logo` na Organization, BreadcrumbList nas páginas internas, Dataset em `/dados-abertos`, termos "empréstimo com garantia de imóvel", "crédito com garantia de imóvel", "refinanciamento" e "portabilidade" onde o assunto já é esse (como-funciona, comparação, quando não vale, FAQ), descrições das páginas pequenas mais completas e JS com `?v=` com cache imutável.

- v4 (19/11, visual do Pix aplicado, só aparência): cartões por campo, número grande à direita, controle com botão brilhante, painel de resultado escuro, frase-resumo âmbar (`r-resumo`), moldura de vidro. Juros em âmbar `#e3a96b`, crédito em azul-petróleo.
- v5 (19/11, benchmark Creditas/NerdWallet/Bankrate): seção "Amortização" (`#amortizacao`) virou "Pagar antes pode poupar milhares de reais": (1) juros vêm primeiro (gráfico anual), (2) simulador de pagar a mais (extra mensal e/ou valor único, em qual ano, reduzindo prazo ou parcela; `calculo.amortizar_antes` = `H.amortizarAntes`, testado Python x JS), (3) gráfico "mesmo valor em momentos diferentes", e três avisos (prazo ou parcela, contrato/CDC art. 52 §2º, comparar com outro uso do dinheiro). Texto jurídico NÃO revisado. Números em reais de hoje, sem custo de oportunidade nem tarifas.

- v6 (19/11): faixa de 3 números abaixo do simulador (quita por volta de, juros por R$ 1 de crédito, taxa equivalente ao ano, com nota do IPCA/BCB) e campo recolhido "Já tem uma proposta? Use a taxa dela" (X% + IPCA, ou "já inclui o IPCA"; válido de 0,3 a 5% a.m.; params `taxa` e `ipca=1` no link; evento `usou-taxa-propria` com `prazo`). Título do passo 2 da amortização: "Amortização: quanto você poupa pagando a mais".

## Próximos passos
1. Decidir melhorias do benchmark: tabela de amortização, custos estimados (só com fonte), renda mínima estimada, "quitar dívida cara".
2. Ver indexação no Google/Bing em alguns dias (`site:homeequity.datalabglobal.com`).
3. Só então começar o Auto Equity (007).

## Testes fora do CI (rodar antes de publicar mudanças no simulador)
- `python testar_navegador.py` — fluxo de ponta a ponta, Chromium + WebKit, computador e celular.
- `python testar_aleatorio.py` — 8 sessões aleatórias × 70 passos (digitar, slider, quitado/financiado, lixo); a cada passo confere parcela, total, % do crédito, barras, cartões do Raio-X, nota da taxa maior e o link compartilhável contra `calculo.py`.
- `python varredura_dispositivos.py` — iPhone SE/13/15, iPad, Pixel, Galaxy (em pé e deitado): rolagem lateral, alvos de toque, diálogo, menu, voltar do navegador.
- Achado conhecido: o Playwright-WebKit avisa "Refused to apply a stylesheet" no console por causa do `<select>` do prazo quando a CSP de produção está ativa (sem efeito funcional; não confirmado em Safari real).
- Mínimo a receber (R$ 50 mil) e teto de crédito (R$ 3 milhões) são limites da interface; o cartão "Receber menos" nunca fica abaixo do mínimo (vira "Receber mais").

## Revisão geral de 20/11/2026 (pedido do dono)
- Números: conta conferida por testes (pytest, navegador, aleatório Chromium+WebKit, 0 falha); taxas do BCB conferidas ao vivo. Taxa do parceiro atualizada de 1,09% para 1,12% ao mês + IPCA (página pública do parceiro em 20/11/2026).
- Menos informação: o simulador de "pagar a mais" (valor extra por mês, amortização única, gráfico por momento, dicas) ficou recolhido em `<details id="det-amsim">`; a parte 1 ("Os juros vêm primeiro") e a tabela por blocos continuam visíveis. Cortou cerca de 2.700 px da home no celular. Os testes que mexem nesses campos abrem o bloco antes.
- SEO: privacidade e termos agora `noindex,follow` e fora do sitemap (texto padrão quase igual nos três simuladores; `SEM_INDICE` no gerador); schema `WebApplication` na home; títulos de sobre/privacidade/termos distintos por produto. Textos do Auto Equity reescritos (a similaridade de 5-gramas com o Home Equity caiu de 0,50 para 0,29 na home e ficou abaixo de 0,40 nas demais páginas indexáveis).
- Rodapé: links cruzados entre Home Equity, Auto Equity e Condomínio.
- Console: o Cloudflare injeta o beacon de Web Analytics (zona datalabglobal.com, "Automatic setup") e a CSP o bloqueia; é só ruído no console, não afeta o uso. Para limpar: ou liberar `static.cloudflareinsights.com` na CSP, ou desligar o setup automático no Cloudflare (decisão do dono).
