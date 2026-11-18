# Simulador de Home Equity — Datalab Global

Idioma: português do Brasil. Estilo: curto, sem jargão, números reais, dizer o que NÃO foi verificado.
Projeto irmão de `../005-pseo-simulador-emprestimo` (mesmas regras de operação). Plano e desenhos aprovados: `../_plano-equity-condominio/` (PLANO.md, mockups, imagens).

## Regras fixas
- **Graphify primeiro, sem o dono pedir.** Antes de ler arquivo/grep: `graphify update .` e `graphify query "..."`. Se pular, avisar na hora.
- Sem gastar dinheiro. Sem postar nem mandar mensagem a pessoas. Nada de CPF/telefone em log, teste ou arquivo.
- **Mensagem agnóstica sobre o parceiro**: "um parceiro de crédito". Sem texto sobre remuneração/comissão e sem citar o nome do parceiro nem de bancos (há teste que barra). Sem ranking.
- Tom calmo sobre a garantia: aviso curto perto do botão, explicação na seção/página própria. Um valor único de parcela (taxa de referência do parceiro); a média do BCB só na nota "E se a taxa for maior?".
- Link de conversão do parceiro (`LINK_PARCEIRO` em `gerador_homeequity.py`) só no botão da tela de confirmação. Não copiar o link de outros produtos para cá.
- Medição: Umami, **ID próprio deste site** (`UMAMI_ID`, hoje vazio = sem script). Eventos: `usou-simulador-homeequity`, `abriu-confirmacao`, `cta-parceiro`, `copiou-link` (só `receber` e `prazo`), `abriu-amortizacao` (`prazo`), `usou-quitar-divida` (`tipo`: pessoal/cheque/rotativo/outra). Não mandar evento de teste ao Umami (nos testes o Umami é bloqueado).
- Sem segredo em arquivo/GitHub. Sem identificar modelo de IA em commits/PRs (só as linhas de atribuição que o sistema mandar). Python 3.10 no CI (sem f-string aninhado). Merge só com `pytest` saindo 0. Fluxo: branch → PR → merge.
- CSP: sem `style=` nem script inline. Barras são SVG com atributos; preenchimento dos sliders usa `data-p` definido por JS.
- Máximo ~15 páginas indexáveis, cada uma com conteúdo próprio.
- Paleta: azul-petróleo acinzentado `#4aa3b5` (escolhido em 18/11 para não se confundir com o verde do imobiliário e o azul de veículos) (Auto Equity é âmbar, Condomínio terracota; imobiliário verde, veículos azul, Pix roxo).

## Comandos
- Gerar: `python gerador_homeequity.py` (saída em `paginas_seo/`, publicada no Cloudflare Pages sem build). O CSS é escrito à mão em `src/estilo.css` (sem Tailwind/npm).
- Testes: `python -m pytest -q` (77). Amortização e "quitar dívida" no navegador: `python testar_amort_quitar.py` (Chromium + WebKit, desktop e celular).
- Seções da home (18/11): "Para onde vai a sua parcela" (amortização anual recolhível, `calculo.amortizacao_anual`) e "Tem uma dívida cara? Veja se vale trocar" (`calculo.comparar_quitacao`, taxas médias BCB 20742/20741/22022 em `REF`; mesmo prazo do simulador; botão leva o valor ao simulador). Navegador de ponta a ponta (Chromium + WebKit, desktop e celular, 160 checagens no total): `python testar_navegador.py` (precisa do Playwright; fora do CI).
- Ícones e imagem de compartilhamento: `python gerar_icones.py` (Playwright + Pillow).
- Taxas do BCB: `python etl_taxas.py` (grava `dados/taxas_referencia.csv`; falha de rede não derruba). Robô semanal em `.github/workflows/atualiza_taxas.yml` (seg 08:00 UTC): taxas, rebuild, pytest, commit, IndexNow.
- Fontes: `conteudo.py` (textos, títulos ≤ 60), `layout.py` (HTML), `src/simulador.js`, `calculo.py` (conta de referência; `calculo.js` é gerado e os testes comparam as duas via Node).

## Fatos do produto (conferidos em 18/11/2026)
- Parceiro divulga: Home Equity a partir de 1,09% a.m. + IPCA, libera até 60% do valor do imóvel, prazo até 20 anos. Taxa de referência = (1+1,09%)·(1+IPCA mensal)−1, IPCA = série SGS 13522 (12 meses) mantido constante: hoje ≈ 1,47% a.m. Parcela fixa (Price) sobre crédito = receber + saldo devedor (financiado). Não inclui IOF, avaliação, registro, seguros.
- Séries BCB: 29976 (garantia real, a.m., mistura imóvel e veículo), 20742/20741/22022 (a.a.), 13522 (IPCA 12m). Fonte e mês aparecem em `/taxas-de-referencia`.
- Cenário padrão da home: imóvel R$ 800.000, receber R$ 250.000, 15 anos → R$ 3.966/mês, total R$ 713.837 (igual ao desenho aprovado).
- Páginas: home + como-funciona, garantia-do-imovel, custos-alem-dos-juros, home-equity-ou-outro-credito, quando-nao-vale-a-pena, taxas-de-referencia, metodologia, sobre, atualizacoes, privacidade, termos (12 no sitemap). Dados: `/dados/taxas-referencia.csv`. Sem página de dados abertos/Kaggle por enquanto.
- Domínio previsto: https://homeequity.datalabglobal.com. IndexNow: chave em `indexnow.py`.

## Estado (18/11/2026)
- Construído, testado e **publicado**: repo `rldelfino/pseo-simulador-homeequity` (main), Cloudflare Pages `pseo-simulador-homeequity` (saída `paginas_seo`, sem build), domínio `homeequity.datalabglobal.com` (CNAME criado pelo Cloudflare). CI verde (62 testes).
- Cloudflare Pages só publica pushes se o app "Cloudflare Workers and Pages" do GitHub tiver acesso ao repositório (Settings > Applications > Configure > Repository access; é uma lista de repositórios, repo novo precisa ser adicionado).
- Umami: plano gratuito só permite 1 site ("Website limit reached"), então `UMAMI_ID` usa o ID compartilhado dos irmãos; filtrar por hostname `homeequity.datalabglobal.com`.
- NÃO verificado: se o formulário do parceiro aceita pré-preenchimento por endereço (hoje abre limpo); iPhone físico; valores mínimo/máximo de crédito do parceiro (o simulador usa mínimo de R$ 50 mil a receber e teto de R$ 3 milhões de crédito como limites de interface, baseados em condições públicas de outras instituições (Creditas R$ 50 mil a R$ 3 mi; Neon até R$ 3 mi), não regra do parceiro); revisão jurídica dos textos.

- Linkado no hub (cartão PT/EN, rodapé, llms.txt) e no rodapé de 002, 003 e 005. Search Console/Bing/IndexNow feitos; DuckDuckGo não tem sitemap (usa o índice do Bing e o rastreador próprio).
- Auditoria e benchmark (18/11): `../_plano-equity-condominio/AUDITORIA-HOME-EQUITY.md`. Conta bate com exemplo público da Creditas (R$ 150 mil, 48 m, IPCA 4,22% → R$ 4.349 / R$ 208,7 mil). Corrigidos: `#simulador` na barra de endereço (Safari voltava ao topo do simulador) e tabelas viram cartões no celular (`data-l` + CSS).

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
