# Benchmark de simuladores — 19/11/2026

**O que foi de fato aberto e lido:** Creditas (página de Home Equity e o início do fluxo de simulação), Nubank (página de empréstimos) e NerdWallet (calculadora de hipoteca, com o cronograma aberto). Bankrate bloqueou com verificação humana (não resolvi) e só li resumos de busca. Calculadora do Cidadão (BC), Mercado Pago, Inter e Credicto/Gyroo **não foram abertos**. Três sites são amostra pequena: trate como pistas, não como mercado inteiro.

## 1. Funcionalidades que ainda não usamos
| Ideia | Quem faz | Esforço | Valor |
|---|---|---|---|
| **Data de quitação** ("Quita em nov/2056") ao lado de parcela e juros totais | NerdWallet | baixo | médio: torna o prazo concreto |
| **Faixa com 3 números** (crédito · juros totais · quita em) acima do gráfico | NerdWallet | baixo | médio |
| **"Tenho outra taxa"**: campo para a taxa da proposta que a pessoa recebeu (hoje só usamos a de referência) | NerdWallet (taxa média / informar a sua / melhor) | médio | alto: é o que quem já tem proposta precisa |
| **Microtexto de confiança junto do botão** ("não pedimos pagamento antecipado", "sem consulta ao score") | Creditas, NerdWallet | baixo | médio. Só dizer o que for verdade no nosso fluxo |
| **Data de atualização/revisão visível** perto do simulador | NerdWallet ("Updated…, fact checked") | baixo | médio, ajuda confiança e SEO |
| **Pré-preenchimento por link**: a Creditas abre o formulário com `?valor-emprestimo=50000` | Creditas | médio (depende do parceiro) | alto: prova que o formato é comum; vale perguntar ao parceiro se aceita valor, prazo e valor do imóvel |
| **Amortizar a mais** (mensal, valor único, prazo ou parcela, momento) | nenhum dos três mostra de forma didática | feito hoje (PR 10) | alto |

## 2. Erros deles que nos alertam
- **Creditas pede CPF, nome, e-mail, data de nascimento, estado civil e renda antes de mostrar qualquer número.** É o maior atrito que vi. Nosso simulador mostra a parcela sem dado pessoal: manter e dizer isso com destaque.
- **Nubank não tem simulador na web**, só portão de CPF e "baixe o app". Quem pesquisa no Google não vê número.
- **NerdWallet mistura impostos e seguro na "parcela mensal"** da manchete e abre um banner de cookies que cobre a tela; segundo resenhas, exige cookies de marketing para recursos. Nós separamos o que é parcela do que não entra e não usamos cookies: manter.
- **Bankrate: verificação humana, anúncios e captura de e-mail** (segundo resenhas; só vi o bloqueio). Não copiar.
- **Taxa de manchete "a partir de"** (Creditas 1,09% a.m.) sem mostrar o efeito do IPCA na parcela. Nossa nota "E se a taxa for maior?" já cobre.

## 3. Elementos de design que podem melhorar o nosso
- **NerdWallet**: resultado em um cartão limpo, rosca com 3 linhas rotuladas ao lado, e botões de taxa em formato de "chips" (média / sua / melhor). Nosso painel já tem rosca; os chips de taxa combinam com a ideia "outra taxa".
- **Creditas**: um único controle ("De quanto você precisa?") e um botão verde-limão grande. Para o celular, vale testar começar só com o valor e abrir o resto depois. Hoje a home tem seis campos de uma vez.
- **Geral**: tudo que nos destaca (comparativo com outras modalidades, quitar dívida cara, Raio-X da renda) eles não têm. O ponto fraco comparado a eles é só o parceiro/marca: não temos selos de confiança nem avaliações; não inventar.

## 4. Sugestão de ordem (se você aprovar)
1. Mesclar o PR 10 (seção de amortização).
2. Faixa "crédito · juros · quita em" + data de atualização perto do simulador.
3. Campo "tenho outra taxa".
4. Perguntar ao parceiro se o link aceita valor, prazo e valor do imóvel por parâmetro.

## 5. O que não verifiquei
Fluxos completos de Creditas após o passo 1, Bankrate por dentro, Inter (app), Calculadora do Cidadão, quais recursos geram mais conversão (não tenho dado). Texto jurídico da amortização (CDC art. 52, § 2º) sem revisão de advogado.
