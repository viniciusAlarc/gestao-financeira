# Decisão D6 — onde o backend roda

> **Dossiê para o dono decidir (P3-3).** Escrito em 2026-11-05 pela sessão s4 da rodada
> `20261105-1014-pendencias`, sob o maestro `gestao-financeira-bd`.
> **Status: aguardando a resposta do dono.** Nada foi criado: sem conta, sem túnel, sem trial, sem VPS.
> Preços em reais pela cotação de 04/11/2026 (US$ 1 = R$ 5,4654; € 1 = R$ 6,1578, calculado a
> partir das duas cotações). Valor final só se confirma no checkout do provedor.

## Resposta curta

Hoje o app só existe na rede de casa. Se você quiser usá-lo fora de casa, há três caminhos:

| Caminho | Em uma frase | Custo recorrente |
|---|---|---|
| **Tailscale** | app de VPN nos dois celulares; nada exposto na internet; HTTPS e PWA funcionam | R$ 0 |
| **Cloudflare Tunnel** | endereço público com login por e-mail; sem app no celular; o tráfego passa pela Cloudflare | R$ 0 + domínio (~R$ 40/ano) |
| **VPS** | app rodando 24h num servidor alugado; não depende do PC de casa | ~R$ 22 a R$ 40/mês + domínio |

Se o uso fora de casa ainda não faz falta, a opção de hoje (só rede local) continua sendo a mais
barata e é o que o plano já prevê para a v1.

## 1. O que está em jogo

Hoje o app roda no WSL do PC de casa (`runserver 0.0.0.0:8000`), em HTTP, e o celular só alcança
quando está na mesma rede. O PWA tem manifest e ícones, mas não tem service worker (decisão de
03/11, registrada; não é defeito).

A decisão D6 muda cinco coisas:

1. **Alcance:** o celular consegue lançar gasto fora de casa?
2. **Disponibilidade:** o app existe quando o PC está desligado?
3. **Exposição:** quem consegue chegar na tela de login?
4. **Privacidade:** o dado financeiro passa ou mora em algum serviço de terceiro?
5. **Custo e manutenção:** quanto custa por mês e quanto trabalho dá para manter.

Critérios usados na recomendação: custo, privacidade do dado, disponibilidade, esforço para duas
pessoas e se o HTTPS (necessário para instalar o PWA) funciona.

## 2. As opções

### Opção 1 — Só na rede de casa (como hoje)

**Como o celular acessa:** `http://<IP-do-PC>:8000`, só no Wi-Fi de casa, com o PC ligado. O IP
precisa estar no `ALLOWED_HOSTS` (é o que o `OPERACAO.md` já manda fazer).

**O que expõe:** só a rede local. Qualquer aparelho no Wi-Fi (inclusive visita) chega na tela de
login. Nada aberto para a internet; o dado não sai do PC.

**O que quebra (PWA/HTTPS):**
- Sem HTTPS, o Chrome do Android não instala de verdade; no máximo cria um atalho. O iPhone
  consegue "Adicionar à Tela de Início", mas sem service worker e sem offline.
- O endereço é um IP que pode mudar. Se mudar, o atalho/PWA para de abrir e o `ALLOWED_HOSTS`
  precisa ser atualizado.
- Fora de casa, o app simplesmente não carrega.

**O que exige:** nada além do que já existe. PC ligado na hora do uso.

**Custo:** R$ 0,00/mês. Se o PC ficaria desligado, não há custo; se ficar ligado só por causa do
app, entra a energia (ver seção 4).

### Opção 2 — Túnel (o app continua no PC de casa)

O túnel não tira o app de casa: ele cria um caminho para o celular chegar no PC. O PC precisa
estar ligado quando você estiver fora. Em troca, não é preciso abrir porta no roteador, e funciona
mesmo atrás de CGNAT ou de IP dinâmico.

#### 2a. Tailscale (Serve) — recomendado se quiser sair de casa

**Como o celular acessa:** instala o app do Tailscale no PC e nos dois celulares, todos na mesma
rede privada (tailnet). O app fica em `https://<nome-da-maquina>.<tailnet>.ts.net`. Funciona em
qualquer lugar com internet; o Tailscale acha o caminho mesmo atrás de NAT.

**O que expõe:** só os aparelhos da tailnet. Não há endereço público. O tráfego é WireGuard de
ponta a ponta: o servidor de coordenação do Tailscale vê metadados (nome dos aparelhos, horários,
IPs), mas não o conteúdo; o relay (DERP) também não consegue ler. Ao ligar o HTTPS, o nome da
máquina e o nome da tailnet aparecem nos logs públicos de certificado (Certificate Transparency);
use um nome de máquina sem informação sensível.

**O que quebra (PWA/HTTPS):** HTTPS funciona, então o PWA pode ser instalado. O convite automático
de instalação do Chrome ainda depende de um service worker, que o app não tem; pelo menu dá para
instalar. No iPhone, "Adicionar à Tela de Início" funciona. Se o Tailscale estiver desligado no
celular, o app não abre.

**O que exige:** conta gratuita no Tailscale; app nos dois celulares e no PC (ou no WSL); MagicDNS
e HTTPS ligados no painel; `tailscale serve --bg 8000`; incluir o endereço `.ts.net` no
`ALLOWED_HOSTS` e no `CSRF_TRUSTED_ORIGINS`. O app roda no WSL; o Tailscale pode rodar no Windows
(apontando para o `localhost:8000` que chega ao WSL) ou dentro do WSL, desde que enxergue a porta.
No Android, o Tailscale ocupa a VPN do aparelho; no iPhone, não dá para usar duas VPNs ao mesmo
tempo.

**Custo:** plano Personal gratuito: 6 usuários, aparelhos ilimitados, uso não comercial. R$ 0,00.
Sem domínio. Se um dia o plano gratuito mudar, o pago é US$ 8/usuário/mês (2 pessoas = ~R$ 87/mês);
não é o caso hoje.

#### 2b. Cloudflare Tunnel (+ Access) — para quem não quer app no celular

**Como o celular acessa:** o `cloudflared` roda no PC e abre uma conexão de saída para a Cloudflare.
Um endereço do seu domínio (ex.: `financas.seudominio.com.br`) aponta para o túnel. O celular abre
esse endereço em qualquer navegador, sem instalar nada. O Cloudflare Access pode exigir um código
enviado por e-mail para as duas contas autorizadas.

**O que expõe:** não abre porta no roteador e esconde o IP de casa, mas o endereço é público na
internet. Sem o Access, qualquer um que descubra o endereço chega na tela de login do Django. Com o
Access, a Cloudflare pede o código por e-mail antes. A Cloudflare termina o TLS na borda dela e
consegue ver o conteúdo que passa; é um terceiro no caminho do dado financeiro.

**O que quebra (PWA/HTTPS):** HTTPS funciona e o PWA pode ser instalado. O Access expira a sessão de
tempos em tempos (configurável); quando expira, o PWA cai na tela de login da Cloudflare. O convite
automático de instalação do Chrome continua dependendo de service worker.

**O que exige:** um domínio no DNS da Cloudflare (dá para registrar no Registro.br e apontar os
nameservers); `cloudflared` rodando como serviço; túnel nomeado com hostname; política do Access
com os dois e-mails; `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS`. O PC precisa estar ligado. O
`trycloudflare.com` (túnel rápido) não serve para o dia a dia: o endereço muda a cada execução e
não tem garantia.

**Custo:** túnel gratuito; Access gratuito até 50 usuários. O único custo é o domínio: ~R$ 40/ano
no Registro.br (.com.br) = R$ 3,33/mês. Se o domínio já existir, o custo marginal é R$ 0.

#### 2c. ngrok — só para teste

**Como o celular acessa:** `ngrok http 8000`; o plano gratuito dá um endereço fixo
`*.ngrok-free.app`. O celular abre esse endereço.

**O que expõe:** endereço público; o ngrok vê o tráfego. O plano gratuito mostra uma página de
aviso antes do app (interstitial), limita a 1 GB de saída e 20.000 requisições por mês, e permite
1 usuário. Para duas pessoas e uso diário, o limite e o aviso atrapalham.

**O que quebra (PWA/HTTPS):** HTTPS funciona, mas o interstitial e o limite mensal tiram a
sensação de app. O plano pago Hobbyist (US$ 10/mês) remove o aviso e sobe para 5 GB / 100.000
requisições.

**O que exige:** conta, agente rodando no PC, PC ligado.

**Custo:** R$ 0 no gratuito (com os limites acima) ou ~R$ 54,65/mês no Hobbyist.

**Veredito:** serve para uma demonstração rápida ou um teste, não para ser o caminho oficial.

### Opção 3 — VPS pequena (o app sai de casa)

**Como o celular acessa:** o app roda num servidor alugado, 24 horas por dia, com um domínio e
HTTPS (Caddy ou Nginx com Let's Encrypt). O celular abre `https://financas.seudominio.com.br` de
qualquer lugar; o PC de casa pode estar desligado.

**O que expõe:** um IP público. Qualquer um chega na tela de login; robôs varrem a internet o
tempo todo. Precisa de firewall, atualizações, senha forte e, de preferência, limite de tentativas
de login. O dado financeiro passa a morar no disco do provedor: no Magalu Cloud fica no Brasil; no
DigitalOcean/Hetzner, fora do país. O provedor tem acesso ao disco; o SQLite não é criptografado
por padrão.

**O que quebra (PWA/HTTPS):** nada no PWA; HTTPS funciona e a instalação é possível. O que muda é
a operação: backup passa a ser obrigatório (um VPS é uma cópia única do dado), e atualizar o
sistema e o Django vira rotina.

**O que exige:** provisionar a máquina, instalar Python 3.12 e as dependências, rodar com gunicorn
e systemd, configurar Caddy/Nginx, firewall, backup e atualizações. Migrar o `db.sqlite3` e o
certificado do Inter para lá (o certificado é segredo, G13) é ação irreversível e precisa da sua
autorização (G3). O teste da integração com o Inter teria de rodar de novo lá.

**Custo:** ver a tabela da seção 4. Ordens de grandeza: DigitalOcean US$ 4 a 6/mês; Hetzner
~€ 6,49/mês com IPv4; Magalu Cloud R$ 34,99/mês (Brasil, impostos inclusos). Some o domínio
(~R$ 40/ano) e, se quiser backup automático, +20% no DigitalOcean/Hetzner.

**Veredito:** só vale se "o app não pode depender do PC ligado" for requisito de verdade. É a
opção mais cara em dinheiro e em manutenção, e a que mais expõe o dado.

## 3. Tabela comparativa

| Critério | 1. Rede de casa | 2a. Tailscale | 2b. Cloudflare Tunnel | 2c. ngrok | 3. VPS |
|---|---|---|---|---|---|
| Funciona fora de casa | não | sim | sim | sim | sim |
| Depende do PC ligado | sim | sim | sim | sim | **não** |
| Como o celular acessa | IP local no Wi-Fi | app Tailscale + URL `.ts.net` | URL pública + código por e-mail | URL pública `*.ngrok-free.app` | URL pública |
| HTTPS / PWA | não / atalho | sim / instala | sim / instala (com login Cloudflare) | sim / instala, com aviso | sim / instala |
| O que expõe | só a LAN | tailnet privada | internet, atrás do Access | internet | internet |
| Terceiro vê o conteúdo? | não | não (só metadados) | sim (Cloudflare, no edge) | sim (ngrok) | sim (provedor do disco) |
| Onde o dado mora | casa | casa | casa | casa | servidor alugado |
| Custo/mês | R$ 0 | R$ 0 | R$ 3,33 (domínio) | R$ 0 ou R$ 54,65 | R$ 21,86 a R$ 39,96 + R$ 3,33 |
| 6 meses | R$ 0 | R$ 0 | R$ 20,00 | R$ 0 ou R$ 327,92 | R$ 151 a R$ 260 |
| Esforço de manutenção | nenhum | baixo | médio | baixo | alto |
| Endereço estável | não (IP muda) | sim | sim | sim (plano free) | sim |

## 4. Custos com os três números do G20

Câmbio de 04/11/2026: US$ 1 = R$ 5,4654; € 1 = R$ 6,1578. Valores arredondados; o provedor cobra
no dia e o cartão pode acrescentar IOF/variação cambial.

### Opções sem custo recorrente

| Opção | (a) custo/dia | (a) custo/mês | (b) ambiente antes → depois | (c) 6 meses sem desligar |
|---|---:|---:|---|---:|
| 1. Rede de casa | R$ 0,00 | R$ 0,00 | R$ 0,00 → R$ 0,00 | R$ 0,00 |
| 2a. Tailscale Personal | R$ 0,00 | R$ 0,00 | R$ 0,00 → R$ 0,00 | R$ 0,00 |

Observação: o plano gratuito do Tailscale é para uso não comercial e cobre 6 usuários. Se os
termos mudarem, o pago é US$ 8/usuário/mês; nada é cobrado sem você aceitar.

### Opções com custo

| Item | (a) custo/dia | (a) custo/mês | (b) ambiente antes → depois | (c) 6 meses sem desligar |
|---|---:|---:|---|---:|
| Domínio .com.br (Registro.br) | R$ 0,11 | R$ 3,33 | R$ 0,00 → R$ 3,33 | R$ 20,00 (renova sozinho todo ano) |
| 2b. Cloudflare Tunnel + Access (com domínio) | R$ 0,11 | R$ 3,33 | R$ 0,00 → R$ 3,33 | R$ 20,00 |
| 2c. ngrok Hobbyist (US$ 10) | R$ 1,82 | R$ 54,65 | R$ 0,00 → R$ 54,65 | R$ 327,92 |
| 3. DigitalOcean US$ 4 (512 MB, 10 GB) | R$ 0,73 | R$ 21,86 | R$ 0,00 → R$ 25,19 com domínio | R$ 151,17 |
| 3. DigitalOcean US$ 6 (1 GB, 25 GB) | R$ 1,09 | R$ 32,79 | R$ 0,00 → R$ 36,13 com domínio | R$ 216,75 |
| 3. Hetzner CX23 ~€ 6,49 com IPv4 (2 vCPU, 4 GB, 40 GB) | R$ 1,33 | R$ 39,96 | R$ 0,00 → R$ 43,30 com domínio | R$ 259,79 |
| 3. Magalu Cloud BV1 1 GB/10 GB (Brasil, impostos inclusos) | R$ 1,17 | R$ 34,99 | R$ 0,00 → R$ 38,32 com domínio | R$ 229,94 |

Notas:
- **Backup do VPS:** no DigitalOcean e no Hetzner, o backup automático custa +20% (~R$ 4,37 a
  R$ 8,00/mês). No Magalu, conferir a opção equivalente. Sem backup, o VPS é uma cópia única do
  dado financeiro.
- **ngrok gratuito:** R$ 0,00, mas 1 GB de saída e 20.000 requisições por mês; para duas pessoas
  pode bastar, mas o aviso (interstitial) e o limite tornam o uso diário frágil.
- **Hetzner:** a página oficial anuncia "a partir de € 5,99/mês, excl. VAT"; o valor da tabela usa
  € 6,49 para incluir o IPv4 (~€ 0,50). Specs de entrada vieram de tabela pública de 2026;
  confirmar no checkout.
- **Cloudflare:** túnel e Access gratuitos (Access até 50 usuários). O domínio é o único custo.
- **VPS "grátis" (Oracle Always Free):** não entra como recomendação. Free tier exige cartão, tem
  limites que mudam e o G20 já registrou susto de fatura em conta de nuvem. Se for considerar,
  entra budget e alerta de gasto antes.

### O custo escondido das opções 1, 2a e 2b: o PC ligado

As opções que mantêm o app em casa só funcionam com o PC ligado. Se ele já fica ligado o dia
inteiro, o custo marginal é R$ 0. Se for ligado só por causa do app, a energia entra na conta:

| Consumo médio do PC | Energia/dia | Energia/mês (a R$ 1,00/kWh) | 6 meses |
|---|---:|---:|---:|
| 30 W (notebook) | 0,72 kWh | R$ 21,60 | R$ 129,60 |
| 100 W (desktop) | 2,40 kWh | R$ 72,00 | R$ 432,00 |
| 150 W (desktop + monitor) | 3,60 kWh | R$ 108,00 | R$ 648,00 |

A tarifa de R$ 1,00/kWh é ordem de grandeza; use a da sua conta de luz. A conclusão que importa:
**deixar um desktop ligado 24h pode custar mais que um VPS pequeno.** Se o PC é um notebook ou já
fica ligado, o túnel continua sendo o caminho mais barato.

## 5. O que muda no projeto em cada opção

| Opção | Código/config | Infra | Risco principal |
|---|---|---|---|
| 1. Rede de casa | nada | nada | IP muda; só funciona em casa |
| 2a. Tailscale | `ALLOWED_HOSTS` + `CSRF_TRUSTED_ORIGINS` com o host `.ts.net` | Tailscale no PC e nos 2 celulares; `tailscale serve --bg 8000` | PC desligado; Tailscale desligado no celular |
| 2b. Cloudflare | `ALLOWED_HOSTS` + `CSRF_TRUSTED_ORIGINS` com o domínio | `cloudflared` como serviço; DNS no Cloudflare; política do Access | PC desligado; sessão do Access expira; Cloudflare vê o conteúdo |
| 2c. ngrok | idem | agente ngrok; PC ligado | limite mensal e interstitial |
| 3. VPS | `ALLOWED_HOSTS` + `CSRF_TRUSTED_ORIGINS`; settings de produção (`DEBUG=False`, estáticos) | VPS, gunicorn, systemd, Caddy, firewall, backup | dado fora de casa; manutenção; migração do banco e do certificado |

Nos quatro casos com HTTPS, além do `ALLOWED_HOSTS`, entra o domínio em `CSRF_TRUSTED_ORIGINS`
(o Django 5 recusa POST de origem HTTPS que não esteja na lista). Se o cookie de sessão for
marcado como `Secure`, também é preciso dizer ao Django que a conexão chega por HTTPS
(`SECURE_PROXY_SSL_HEADER`); isso é detalhe de implementação, não muda a decisão.

## 6. Recomendação

**Para a v1, mantenha a opção 1 (só rede de casa).** É o que o plano já prevê, custa R$ 0 e não
expõe nada. A fase 8 do plano só entra se a fase 6 (uso real a dois, P3-9) mostrar que a
limitação de "só em casa" incomoda de verdade. Decidir agora o que ainda não dói é gastar atenção
e dinheiro sem dado.

**Se você já sabe que quer lançar gasto fora de casa, a recomendação é o Tailscale (2a).** Por quê:
- custa R$ 0 e não tem domínio para renovar;
- não expõe nada na internet: só os aparelhos da tailnet chegam;
- o tráfego é criptografado de ponta a ponta; a Tailscale não vê o conteúdo;
- resolve o HTTPS, que é o que falta para instalar o PWA;
- funciona atrás de CGNAT e de IP dinâmico, sem abrir porta no roteador;
- o custo real é instalar o app nos dois celulares e manter o PC ligado quando estiver fora.

**O Cloudflare Tunnel (2b) é o plano B** se a instalação do Tailscale nos dois celulares for atrito
demais (por exemplo, a esposa não quiser manter uma VPN ligada). Em troca, você paga ~R$ 40/ano de
domínio e aceita que a Cloudflare vê o conteúdo no edge. O Access reduz o risco de exposição, mas
não elimina o terceiro no caminho.

**O VPS (3) só se "o PC não pode ficar ligado" for requisito.** É a opção mais cara em dinheiro e
em manutenção, e a única que tira o dado de casa. Se for por esse caminho, entra budget e alerta
de gasto no provedor desde o primeiro dia (G20), e o backup é obrigatório.

**O ngrok (2c) não é caminho oficial:** serve para testar rápido, não para o dia a dia.

## 7. A pergunta exata

Responda com uma letra (e, se for B, C ou D, a segunda pergunta):

> **P3-3 · D6 — para a v1, onde o app deve rodar?**
>
> **A)** Só na rede de casa, como hoje, e reavaliar depois da fase 6. (R$ 0; celular só em casa.)
>
> **B)** Tailscale, para usar fora de casa. (R$ 0; instalar o Tailscale nos dois celulares e no PC;
> nada exposto na internet; HTTPS e PWA.) **Recomendado se quiser sair de casa agora.**
>
> **C)** Cloudflare Tunnel, para usar fora de casa sem app no celular. (R$ 0 + domínio de ~R$ 40/ano;
> o tráfego passa pela Cloudflare.)
>
> **D)** VPS, para não depender do PC ligado. (~R$ 22 a R$ 40/mês + domínio; dado financeiro num
> servidor alugado; manutenção e backup por sua conta.)
>
> **Se B, C ou D:** o PC de casa pode ficar ligado quando você estiver fora? (B e C dependem disso;
> D não.)

Depois da resposta, a decisão entra neste documento com data e o item P3-3 sai do `PENDENCIAS.md`
(o maestro consolida). Se a resposta for A, a decisão é "manter a opção 1 na v1" e a fase 8 fica
para quando o uso real pedir.

## 8. Registro da decisão

| Campo | Valor |
|---|---|
| Data da decisão | 2026-11-17 |
| Escolha | **PythonAnywhere, plano Beginner (gratuito)** — opção nova, fora das A a D |
| O PC pode ficar ligado fora de casa? | não é requisito: o app passa a rodar no servidor |
| Observações | Decidida para publicar o MVP a dois, sem custo recorrente. Passo a passo em `03-deploy-pythonanywhere.md`. |

**Por que fora das A a D.** O dossiê foi escrito em 2026-11-05 supondo que o app continuaria em
casa; o PythonAnywhere é um serviço gerenciado (PaaS), não um túnel nem uma VPS. Ele entrega Django e
SQLite persistentes com HTTPS sem configuração de servidor, que é o que o MVP pedia.

**O que a escolha aceita:**

- o web app expira a cada mês (contas novas) e precisa de renovação manual na aba Web;
- 100 s de CPU por dia, suficiente para duas pessoas;
- a conta só acessa APIs da allowlist; como `api.pluggy.ai` está nela, a importação da Pluggy
  (fase 7) **pode rodar** no plano grátis; outras APIs dependem da lista;
- o banco é cópia única no servidor; o backup passa a ser manual e semanal.

**Quando rever.** Se a Pluggy for usada no servidor ou a renovação mensal incomodar, as alternativas
são o plano Developer do PythonAnywhere (US$ 10/mês, com internet externa irrestrita) ou o Railway
(US$ 5/mês, com volume persistente). A opção D (VPS) continua valendo para quem quiser o dado no
Brasil, com o custo e a manutenção já registrados neste dossiê.

## 9. Fontes e data de consulta

Consultadas em 05/11/2026. Preços e limites mudam; o valor final é o do checkout.

| Assunto | Fonte |
|---|---|
| Tailscale: planos, 6 usuários, aparelhos ilimitados | https://tailscale.com/pricing |
| Tailscale Funnel: todos os planos, URL `.ts.net`, TLS | https://tailscale.com/kb/1223/funnel |
| Tailscale Serve: só dentro da tailnet | https://tailscale.com/kb/1242/tailscale-serve |
| Tailscale HTTPS: Let's Encrypt, logs de Certificate Transparency | https://tailscale.com/kb/1153/enabling-https |
| Cloudflare Tunnel: conexão de saída, sem porta de entrada | https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/ |
| Cloudflare: túnel rápido muda de URL e não é para produção | https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/do-more-with-tunnels/trycloudflare/ |
| Cloudflare: DNS do túnel precisa estar na mesma conta (domínio na Cloudflare) | https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/routing-to-tunnel/dns/ |
| Cloudflare Zero Trust: plano gratuito até 50 usuários | https://www.cloudflare.com/plans/zero-trust-services/ |
| ngrok: planos e preços | https://ngrok.com/pricing |
| ngrok: limites do plano gratuito | https://ngrok.com/docs/pricing-limits/free-plan-limits |
| DigitalOcean: droplets | https://www.digitalocean.com/pricing/droplets |
| Magalu Cloud: tipos e preços de VM | https://docs.magalu.cloud/docs/computing/virtual-machine/instance-types-and-pricing/pricing/ |
| Hetzner: preço de entrada (conferir a tabela ao vivo) | https://www.hetzner.com/cloud/ |
| Registro.br: preço do .com.br (conferir no site) | https://registro.br/dominio/registro/ |
| Câmbio de 04/11/2026 | https://api.frankfurter.dev/v1/latest?from=USD&to=BRL,EUR |

## 10. O que este documento não fez

- Não criou conta, túnel, trial, VPS nem domínio.
- Não alterou código, configuração, `PENDENCIAS.md`, `PROGRESS.md` nem `docs-dev/painel.json`.
- Não decidiu: a escolha é do dono. A recomendação é insumo, não decisão.
- Não mediu o consumo do PC de casa; a tabela de energia é ordem de grandeza, para mostrar que
  "grátis" tem custo quando o PC precisa ficar ligado.
