# PRD — MariaBicoBot (Telegram) | Curadoria Shopee + Link Rastreável (Afiliado) | Python

## Metadata

| Campo | Valor |
|-------|-------|
| **Autor** | Gabriel Ramos |
| **Versão** | 1.0 |
| **Status** | Planning |
| **Criado em** | 13/01/2026 |
| **Última atualização** | 13/01/2026 |
| **Domínio** | mariabicobot.proframos.com |
| **Stack principal** | Python 3.12, python-telegram-bot v20+, SQLite, Docker |

### Histórico de Versões
| Versão | Data | Mudanças | Autor |
|--------|------|----------|-------|
| 1.0 | 13/01/2026 | Versão inicial do PRD | Gabriel Ramos |

***

## 1) Resumo Executivo
Desenvolver um bot no Telegram, em Python, para uso pessoal, que:
1) Seleciona periodicamente produtos Shopee com melhor equilíbrio entre **comissão** e **preço atrativo ao cliente** (desconto/valor), usando a Shopee Affiliate GraphQL API.
2) Publica no **grupo privado** do Telegram uma mensagem pronta para copiar/colar, contendo **título + preço + desconto + comissão estimada + link rastreável**.
3) Disponibiliza um fluxo manual via botão/comando: o usuário envia um link de produto e o bot retorna o **short link rastreável** (com subIds padronizados).

**Problema**: Processo manual de curadoria de produtos Shopee consome 2h diárias, com risco de erro na geração de links rastreáveis e perda de rastreabilidade por campanha.

**Solução**: Automação completa da curadoria com rankeamento inteligente e geração automática de links rastreáveis com subIds padronizados.

**Valor esperado**: Redução de 2h para 5min no tempo de curadoria diária + rastreabilidade 100% confiável por canal/campanha.

***

## 2) Objetivos e Métricas de Sucesso

### Objetivos de Negócio
- **Eficiência**: Reduzir tempo de curadoria manual de 120min para 5min/dia
- **Qualidade**: Garantir 100% dos produtos publicados possuem comissão >= 8% e desconto >= 15%
- **Rastreabilidade**: 100% dos links com subIds padronizados por canal/campanha/lote
- **Consistência**: Zero erros manuais na geração de links ou formatação de mensagens

### Métricas SMART (Success Metrics)

| Métrica | Target | Medição | Frequência |
|---------|--------|---------|------------|
| **API Success Rate** | >= 99% | Rolling window 7 dias | Diária |
| **Curadoria Execution Time** | < 60s (p95) | Para lote de 200 itens | Por execução |
| **Link Generation Success** | 100% | Produtos aprovados com short link | Por execução |
| **Deduplication Accuracy** | 0 duplicatas | Por batch/período configurado | Por execução |
| **Time-to-Market** | < 5min | Da execução até publicação no grupo | Por curadoria |
| **Sistema Uptime** | >= 99.5% | Container health status | Semanal |

### Métricas Operacionais (Logs)
- Total de itens fetched por execução
- Taxa de aprovação (itens aprovados / itens fetched)
- Latência média da API Shopee
- Rate limit utilizado (requests/hora)

***

## 3) Usuários e Personas

### Persona Primária: Afiliado Solo (Gabriel Ramos)

**Background**
- Coordenador Administrativo e Professor
- Afiliado Shopee em tempo parcial
- Gerencia divulgação em grupos Telegram privados

**Contexto de Uso**
- **Quando**: Período noturno (20h-22h) para preparar posts do dia seguinte
- **Onde**: MacBook M3, acesso via Telegram Desktop/Mobile
- **Frequência**: 2-3x por dia (manhã, tarde, noite)

**Necessidades**
- Curadoria rápida sem análise manual produto por produto
- Links rastreáveis automáticos para medir performance por campanha
- Mensagens prontas para copy/paste em múltiplos canais

**Pain Points Atuais**
- 2h diárias navegando manualmente no painel Shopee Affiliate
- Risco de esquecer de adicionar subIds nos links
- Dificuldade em identificar quais produtos já foram divulgados
- Formatação manual inconsistente das mensagens

**Expectativas**
- "Quero acordar e ver produtos já curados prontos para publicar"
- "Preciso saber exatamente qual campanha gerou cada conversão"
- "Links devem funcionar 100% e serem curtos para WhatsApp/SMS também"

### Permissões
- **Admin único**: Seu `telegram_user_id` (allowlist hardcoded)
- Bot só responde a:
  - Comandos diretos (DM) do admin
  - Mensagens no grupo autorizado se autor for o admin

***

## 4) Escopo

### In Scope (MVP - Fase 1)

#### ✅ Curadoria Automática
- Busca via `productOfferV2` com keywords/categorias configuráveis
- Rankeamento local por score (comissão + desconto - preço)
- Geração de short links com subIds padronizados
- Publicação consolidada no grupo (Top N)
- Agendamento via APScheduler (6h/12h/24h configurável)

#### ✅ Conversão Manual
- Interface com botões inline (InlineKeyboardMarkup)
- Validação e normalização de URLs Shopee
- Geração de short link on-demand
- Texto formatado pronto para copiar

#### ✅ Persistência
- SQLite para histórico, links, configurações
- Deduplicação por `itemId` + período configurável
- Logs de execução e auditoria

#### ✅ Deploy
- Docker + Portainer Stack
- Network `ProfRamosNet` + Traefik ready
- Secrets via environment variables
- Volume persistente para `/data`

### Out of Scope

#### ❌ Não será implementado (nunca ou fase 3+)
- Suporte a múltiplos usuários/admins
- Integração com outras plataformas de afiliados (Amazon, Mercado Livre)
- Painel web de administração
- Notificações push de conversões em tempo real
- Machine learning para predição de conversão
- Integração com CRM ou analytics externo

#### 🔄 Fora do MVP (Fase 2)
- Configuração dinâmica via comandos (editar keywords/thresholds no bot)
- Coleta e análise de `conversionReport` + `validatedReport`
- Webhook mode (MVP usa polling)
- Feed público (CSV/JSON) para vitrine externa
- Multi-grupos e multi-canais

***

## 5) Requisitos Funcionais (User Stories)

### RF-01: Curadoria Automática

**User Story**
> **Como** afiliado Shopee,  
> **Quero** que o bot execute curadoria automaticamente a cada 12h,  
> **Para que** eu sempre tenha produtos frescos sem intervenção manual.

**Critérios de Aceitação**
- ✅ Executa via APScheduler no intervalo configurado (default: 12h)
- ✅ Consulta `productOfferV2` com parâmetros: keywords, categorias, limit/page
- ✅ Aplica filtros mínimos: `commissionRate >= 8%`, `discount >= 15%`, `priceMax` (se configurado)
- ✅ Calcula score local: `(commission * 1.0) + (discount * 0.5) - (price * 0.02)`
- ✅ Ordena por score decrescente e seleciona Top N (default: 10)
- ✅ Gera short link com subIds: `[tg, grupo1, curadoria, {timestamp}, {keyword}]`
- ✅ Envia mensagem consolidada no grupo com Top N produtos
- ✅ Registra execução em `runs` table
- ✅ Deduplica: não reenvia `itemId` publicado nos últimos 7 dias

**Parâmetros Configuráveis** (via `settings` table)
```json
{
  "keywords": ["fone bluetooth", "smartwatch", "carregador rápido"],
  "categories": [11043380],
  "thresholds": {
    "commission_rate_min": 0.08,
    "commission_min_brl": 8.00,
    "discount_min_pct": 15,
    "price_max_brl": 250,
    "sales_min": 50,
    "rating_min": 4.7
  },
  "weights": {
    "commission": 1.0,
    "discount": 0.5,
    "price": 0.02
  },
  "top_n": 10,
  "max_pages": 5,
  "page_limit": 50,
  "dedup_days": 7,
  "schedule_cron": "0 */12 * * *"
}
```

***

### RF-02: Conversão Manual de Link

**User Story**
> **Como** afiliado,  
> **Quero** converter um link Shopee específico em link rastreável,  
> **Para que** eu possa divulgar produtos encontrados fora do bot.

**Critérios de Aceitação**
- ✅ Comando `/converter` ou botão "Converter Link" ativa modo listening
- ✅ Bot responde: "Envie o link do produto Shopee"
- ✅ Valida URL (domínios: `shopee.com.br`, `shope.ee`)
- ✅ Normaliza URL para formato padrão
- ✅ Consulta cache de short links (tabela `links` por `origin_url`)
- ✅ Se não existe, chama `generateShortLink` com subIds: `[tg, manual, {timestamp}]`
- ✅ Retorna mensagem formatada com short link + texto pronto
- ✅ Salva em `links` table para reutilização
- ✅ Timeout de 60s se usuário não enviar link

**Fluxo de Erro**
- URL inválida: "❌ Link inválido. Envie um link Shopee válido."
- Falha na API: "⚠️ Erro ao gerar link. Tente novamente em instantes."

***

### RF-03: Menu Principal e Navegação

**User Story**
> **Como** usuário admin,  
> **Quero** acessar todas as funcionalidades via menu interativo,  
> **Para que** eu não precise memorizar comandos.

**Critérios de Aceitação**
- ✅ Comando `/start` ou `/menu` exibe menu com botões inline
- ✅ Botões: "🤖 Curadoria Agora", "🔗 Converter Link", "📊 Status", "⚙️ Ajuda"
- ✅ Callback handlers para cada botão
- ✅ Apenas admin autorizado pode acionar
- ✅ Mensagens de usuários não autorizados são ignoradas silenciosamente

***

### RF-04: Status e Monitoramento

**User Story**
> **Como** admin,  
> **Quero** consultar o status das execuções,  
> **Para que** eu possa verificar se tudo está funcionando corretamente.

**Critérios de Aceitação**
- ✅ Comando `/status` ou botão "📊 Status"
- ✅ Retorna:
  - Última execução (data/hora)
  - Itens avaliados / aprovados / enviados
  - Taxa de sucesso da última execução
  - Próxima execução agendada
  - Erros resumidos (se houver)
  - Uptime do container
  - Uso de rate limit (requests/hora)

**Exemplo de Resposta**
```
📊 Status do MariaBicoBot

✅ Sistema operacional
🕐 Última curadoria: 13/01/2026 08:00
📦 Avaliados: 245 | Aprovados: 18 | Enviados: 10
✅ Taxa de sucesso: 100%
⏭️ Próxima execução: 13/01/2026 20:00
⚡ Rate limit: 127/2000 req/h
```

***

### RF-05: Geração de Short Link Rastreável

**Regras de SubIds** (padronização obrigatória)
```python
subIds = [
    "tg",                    # Canal: Telegram
    f"grupo{group_hash}",    # Grupo (hash curto do group_id)
    campaign_type,           # "curadoria" ou "manual"
    timestamp,               # YYYYMMDD_HHMM
    tag                      # Keyword ou categoria curta
]
```

**Cache de Links**
- Consultar tabela `links` por `origin_url` antes de chamar API
- TTL: 30 dias (após isso, regerar)
- Evita esgotar rate limit com produtos recorrentes

***

### RF-06: Formatação de Mensagens

**User Story**
> **Como** afiliado,  
> **Quero** mensagens padronizadas e prontas para copiar,  
> **Para que** eu mantenha consistência visual em todos os posts.

**Template (HTML)**
```html
🛒 <b>{productName}</b>

💰 R$ {priceMin} | 🔻 {discount}% OFF
💸 Comissão: R$ {commission} ({commissionRate}%)

🔗 {shortLink}

#{keyword} #shopee #oferta
```

**Mensagem Consolidada (Top N)**
```
🤖 Curadoria MariaBicoBot
📅 {date} às {time}

🏆 Top 10 Produtos Selecionados:

---
1️⃣ [Produto 1 formatado]
---
2️⃣ [Produto 2 formatado]
---
...
```

***

## 6) Wireframes e Especificações de UI

### 6.1) Menu Principal

**Comando**: `/start` ou `/menu`

**Wireframe (Telegram)**
```
┌─────────────────────────────────────┐
│  🤖 MariaBicoBot                    │
│  Bot de Curadoria Shopee Afiliados  │
│                                      │
│  Escolha uma opção:                 │
│                                      │
│  ┌─────────────┐ ┌─────────────┐   │
│  │ 🤖 Curadoria│ │ 🔗 Converter│   │
│  │    Agora    │ │    Link     │   │
│  └─────────────┘ └─────────────┘   │
│                                      │
│  ┌─────────────┐ ┌─────────────┐   │
│  │  📊 Status  │ │  ⚙️ Ajuda   │   │
│  └─────────────┘ └─────────────┘   │
└─────────────────────────────────────┘
```

**Código de Implementação**
```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Exibe menu principal"""
    keyboard = [
        [
            InlineKeyboardButton("🤖 Curadoria Agora", callback_data="curate_now"),
            InlineKeyboardButton("🔗 Converter Link", callback_data="convert_link"),
        ],
        [
            InlineKeyboardButton("📊 Status", callback_data="status"),
            InlineKeyboardButton("⚙️ Ajuda", callback_data="help"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "🤖 <b>MariaBicoBot</b>\n"
        "Bot de Curadoria Shopee Afiliados\n\n"
        "Escolha uma opção:"
    )
    
    await update.message.reply_text(
        text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
```

***

### 6.2) Mensagem de Produto Individual

**Wireframe (Telegram HTML)**
```
┌─────────────────────────────────────────────┐
│ 🛒 Fone Bluetooth 5.3 TWS Pro XYZ          │
│                                             │
│ 💰 R$ 89,90 | 🔻 35% OFF                   │
│ 💸 Comissão: R$ 12,50 (14%)                │
│                                             │
│ 🔗 https://shope.ee/5AbC123Xyz             │
│                                             │
│ #fonebluetooth #shopee #oferta             │
└─────────────────────────────────────────────┘
```

**Código de Implementação**
```python
def format_product_message(product: dict, short_link: str) -> str:
    """Formata mensagem de produto individual"""
    return (
        f"🛒 <b>{product['productName'][:80]}</b>\n\n"
        f"💰 R$ {product['priceMin']:.2f} | 🔻 {product['priceDiscountRate']}% OFF\n"
        f"💸 Comissão: R$ {product['commission']:.2f} "
        f"({product['commissionRate']*100:.1f}%)\n\n"
        f"🔗 {short_link}\n\n"
        f"#{product['keyword'].replace(' ', '')} #shopee #oferta"
    )
```

***

### 6.3) Mensagem Consolidada (Top N)

**Wireframe (Telegram HTML)**
```
┌──────────────────────────────────────────────┐
│ 🤖 Curadoria MariaBicoBot                   │
│ 📅 13/01/2026 às 14:30                      │
│                                              │
│ 🏆 Top 10 Produtos Selecionados:            │
│                                              │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│ 1️⃣ Fone Bluetooth TWS Pro                   │
│ 💰 R$ 89,90 | 🔻 35% | 💸 R$ 12,50         │
│ 🔗 https://shope.ee/5AbC1                   │
│                                              │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│ 2️⃣ Smartwatch Y68 Plus                      │
│ 💰 R$ 149,90 | 🔻 42% | 💸 R$ 18,00        │
│ 🔗 https://shope.ee/7XyZ2                   │
│                                              │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│ 3️⃣ Carregador Turbo 65W GaN                 │
│ 💰 R$ 79,90 | 🔻 28% | 💸 R$ 9,60          │
│ 🔗 https://shope.ee/9PqR3                   │
│                                              │
│ [...continua até Top 10]                    │
│                                              │
│ 📊 Avaliados: 245 | Aprovados: 18           │
└──────────────────────────────────────────────┘
```

**Código de Implementação**
```python
async def send_curated_products(context: ContextTypes.DEFAULT_TYPE, products: list):
    """Envia lote consolidado de produtos"""
    header = (
        "🤖 <b>Curadoria MariaBicoBot</b>\n"
        f"📅 {datetime.now().strftime('%d/%m/%Y às %H:%M')}\n\n"
        f"🏆 Top {len(products)} Produtos Selecionados:\n"
    )
    
    items = []
    for i, p in enumerate(products, 1):
        item = (
            f"\n{'━' * 40}\n"
            f"{i}️⃣ <b>{p['productName'][:50]}</b>\n"
            f"💰 R$ {p['priceMin']:.2f} | 🔻 {p['priceDiscountRate']}% | "
            f"💸 R$ {p['commission']:.2f}\n"
            f"🔗 {p['shortLink']}"
        )
        items.append(item)
    
    footer = (
        f"\n\n📊 Avaliados: {context.bot_data['total_fetched']} | "
        f"Aprovados: {context.bot_data['total_approved']}"
    )
    
    message = header + "".join(items) + footer
    
    await context.bot.send_message(
        chat_id=TARGET_GROUP_ID,
        text=message,
        parse_mode="HTML",
        disable_web_page_preview=True
    )
```

***

### 6.4) Fluxo de Conversão Manual

**Passo 1: Acionamento**
```
┌─────────────────────────────────────┐
│  Você clicou em: 🔗 Converter Link  │
│                                      │
│  📎 Envie o link do produto Shopee  │
│  que deseja converter.              │
│                                      │
│  ⏱️ Aguardando link... (60s)        │
└─────────────────────────────────────┘
```

**Passo 2: Processamento**
```
┌─────────────────────────────────────┐
│  Você enviou:                       │
│  https://shopee.com.br/product...   │
│                                      │
│  ⚙️ Gerando link rastreável...      │
└─────────────────────────────────────┘
```

**Passo 3: Resposta**
```
┌─────────────────────────────────────────────┐
│ ✅ Link convertido com sucesso!            │
│                                             │
│ 🛒 Produto XYZ                              │
│ 💰 R$ 129,90 | 🔻 25% OFF                   │
│ 💸 Comissão: R$ 15,60 (12%)                │
│                                             │
│ 🔗 https://shope.ee/abc123xyz               │
│                                             │
│ 📋 Texto copiado automaticamente!          │
│                                             │
│  ┌─────────────────┐                       │
│  │  🔙 Voltar Menu │                       │
│  └─────────────────┘                       │
└─────────────────────────────────────────────┘
```

**Código de Implementação**
```python
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

# Estados da conversação
AWAITING_LINK = 1

async def convert_link_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia fluxo de conversão"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📎 <b>Converter Link</b>\n\n"
        "Envie o link do produto Shopee que deseja converter.\n\n"
        "⏱️ Aguardando link... (60s)",
        parse_mode="HTML"
    )
    
    return AWAITING_LINK

async def process_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa link enviado"""
    url = update.message.text.strip()
    
    # Validação
    if not is_valid_shopee_url(url):
        await update.message.reply_text(
            "❌ Link inválido. Envie um link Shopee válido.\n\n"
            "Exemplo: https://shopee.com.br/product/..."
        )
        return AWAITING_LINK
    
    # Indicador de processamento
    msg = await update.message.reply_text("⚙️ Gerando link rastreável...")
    
    try:
        # Gera short link
        short_link = await generate_short_link(url, campaign="manual")
        
        # Formata resposta
        keyboard = [[InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await msg.edit_text(
            "✅ <b>Link convertido com sucesso!</b>\n\n"
            f"🔗 {short_link}\n\n"
            "📋 Copie e compartilhe!",
            parse_mode="HTML",
            reply_markup=reply_markup
        )
        
        return ConversationHandler.END
        
    except Exception as e:
        await msg.edit_text(
            "⚠️ <b>Erro ao gerar link</b>\n\n"
            f"Detalhes: {str(e)}\n\n"
            "Tente novamente em instantes.",
            parse_mode="HTML"
        )
        return ConversationHandler.END
```

***

### 6.5) Status Dashboard

**Wireframe**
```
┌──────────────────────────────────────────────┐
│ 📊 Status do MariaBicoBot                   │
│                                              │
│ ✅ Sistema operacional                      │
│ 🕐 Uptime: 5d 12h 34m                       │
│                                              │
│ 📦 Última Curadoria                         │
│ • Data: 13/01/2026 08:00                    │
│ • Avaliados: 245 produtos                   │
│ • Aprovados: 18 produtos                    │
│ • Enviados: 10 produtos                     │
│ • Taxa sucesso: 100%                        │
│                                              │
│ ⏭️ Próxima Execução                         │
│ • Agendada para: 13/01/2026 20:00          │
│ • Tipo: Curadoria automática                │
│                                              │
│ ⚡ Rate Limit API Shopee                    │
│ • Usado: 127 / 2000 req/h                   │
│ • Disponível: 1873 req/h                    │
│                                              │
│ 💾 Banco de Dados                           │
│ • Produtos únicos: 1.247                    │
│ • Links gerados: 3.891                      │
│ • Envios realizados: 2.104                  │
│                                              │
│ ⚠️ Erros (últimas 24h): 0                   │
│                                              │
│  ┌────────────┐ ┌────────────┐             │
│  │ 🔄 Atualizar│ │ 🔙 Menu   │             │
│  └────────────┘ └────────────┘             │
└──────────────────────────────────────────────┘
```

**Código de Implementação**
```python
async def show_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Exibe status do sistema"""
    query = update.callback_query
    await query.answer()
    
    # Busca dados
    stats = get_system_stats()
    last_run = get_last_run()
    next_run = get_next_scheduled_run()
    rate_limit = get_rate_limit_usage()
    db_stats = get_database_stats()
    
    keyboard = [
        [
            InlineKeyboardButton("🔄 Atualizar", callback_data="status"),
            InlineKeyboardButton("🔙 Menu", callback_data="menu"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "📊 <b>Status do MariaBicoBot</b>\n\n"
        f"{'✅' if stats['is_healthy'] else '⚠️'} Sistema {'operacional' if stats['is_healthy'] else 'com problemas'}\n"
        f"🕐 Uptime: {stats['uptime']}\n\n"
        
        "📦 <b>Última Curadoria</b>\n"
        f"• Data: {last_run['timestamp']}\n"
        f"• Avaliados: {last_run['fetched']} produtos\n"
        f"• Aprovados: {last_run['approved']} produtos\n"
        f"• Enviados: {last_run['sent']} produtos\n"
        f"• Taxa sucesso: {last_run['success_rate']}%\n\n"
        
        "⏭️ <b>Próxima Execução</b>\n"
        f"• Agendada para: {next_run['scheduled_at']}\n"
        f"• Tipo: {next_run['type']}\n\n"
        
        "⚡ <b>Rate Limit API Shopee</b>\n"
        f"• Usado: {rate_limit['used']} / 2000 req/h\n"
        f"• Disponível: {rate_limit['available']} req/h\n\n"
        
        "💾 <b>Banco de Dados</b>\n"
        f"• Produtos únicos: {db_stats['unique_products']:,}\n"
        f"• Links gerados: {db_stats['total_links']:,}\n"
        f"• Envios realizados: {db_stats['total_sent']:,}\n\n"
        
        f"⚠️ Erros (últimas 24h): {stats['errors_24h']}"
    )
    
    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=reply_markup
    )
```

***

## 7) Requisitos Não Funcionais

### Segurança (NFR-SEC)

**NFR-SEC-01: Secrets Management**
- Todas as credenciais via variáveis de ambiente
- Nunca hardcode: `TELEGRAM_BOT_TOKEN`, `SHOPEE_APP_ID`, `SHOPEE_SECRET`
- `.env` no `.dockerignore` e `.gitignore`

**NFR-SEC-02: Access Control**
- Allowlist hardcoded: `ADMIN_TELEGRAM_USER_ID`
- Bot ignora silenciosamente mensagens de usuários não autorizados
- Logs não devem expor `user_id` de requisições rejeitadas

**NFR-SEC-03: Input Sanitization**
- Validação rígida de URLs (regex + domínio)
- Limites de tamanho: URLs < 2048 chars
- Escape de HTML em mensagens user-generated

***

### Confiabilidade (NFR-REL)

**NFR-REL-01: Retry Logic**
- HTTP requests com retry exponential backoff (3 tentativas)
- Delays: 1s, 2s, 4s
- Timeout por request: 10s

**NFR-REL-02: Rate Limit Handling**
- Cache de short links por `origin_url` (TTL: 30 dias)
- Limite de pages por execução: `max_pages` (default: 5)
- Monitoramento contínuo: `used_requests / 2000`

**NFR-REL-03: Graceful Degradation**
- Se API Shopee falhar, registrar erro e continuar execução
- Se Telegram falhar, retry com backoff antes de desistir
- Container health check: ping interno a cada 30s

***

### Performance (NFR-PERF)

**NFR-PERF-01: Execution Time**
- Curadoria completa (200 itens): < 60s (p95)
- Conversão manual: < 3s (p99)
- Database queries: < 100ms (p99)

**NFR-PERF-02: Memory Footprint**
- Container max memory: 512MB
- SQLite database: < 100MB (1 ano de operação)

**NFR-PERF-03: Database Optimization**
- Índices: `products_seen(item_id)`, `links(origin_url)`, `sent_messages(item_id, group_id)`
- VACUUM automático: semanal

***

### Observabilidade (NFR-OBS)

**NFR-OBS-01: Structured Logging**
- Formato JSON no stdout
- Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Campos obrigatórios: `timestamp`, `level`, `component`, `message`, `context`

```json
{
  "timestamp": "2026-01-13T14:30:00-03:00",
  "level": "INFO",
  "component": "curator",
  "message": "Curadoria executada com sucesso",
  "context": {
    "fetched": 245,
    "approved": 18,
    "sent": 10,
    "duration_seconds": 42.3
  }
}
```

**NFR-OBS-02: Métricas Expostas**
- Contadores via logs (parseable pelo Portainer/Loki)
- Métricas: `curations_total`, `products_fetched`, `products_approved`, `links_generated`, `errors_total`

**NFR-OBS-03: Health Check**
- Endpoint HTTP (opcional): `/health` retorna 200 se operacional
- Ou: processo watchdog interno (check database + scheduler)

***

## 8) Arquitetura Técnica

### Componentes

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Container                      │
│  ┌───────────────────────────────────────────────────┐ │
│  │           MariaBicoBot Application                │ │
│  │                                                    │ │
│  │  ┌──────────────┐      ┌──────────────┐          │ │
│  │  │   Telegram   │◄─────┤  APScheduler │          │ │
│  │  │   Bot (PTB)  │      │   (Cron)     │          │ │
│  │  └───────┬──────┘      └──────────────┘          │ │
│  │          │                                         │ │
│  │          ▼                                         │ │
│  │  ┌──────────────────────────────────┐             │ │
│  │  │      Core Business Logic         │             │ │
│  │  │  • Curator                       │             │ │
│  │  │  • Link Generator                │             │ │
│  │  │  • Message Formatter             │             │ │
│  │  │  • Deduplicator                  │             │ │
│  │  └────────┬─────────────────────────┘             │ │
│  │           │                                        │ │
│  │           ▼                                        │ │
│  │  ┌──────────────┐      ┌──────────────┐          │ │
│  │  │ Shopee API   │      │   SQLite DB  │          │ │
│  │  │  Client      │      │  /data/...   │          │ │
│  │  └──────────────┘      └──────────────┘          │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
  ┌─────────────┐              ┌──────────────┐
  │  Telegram   │              │  Shopee API  │
  │  Bot API    │              │   GraphQL    │
  └─────────────┘              └──────────────┘
```

### Stack Tecnológico

| Componente | Tecnologia | Versão | Justificativa |
|------------|-----------|--------|---------------|
| **Runtime** | Python | 3.12 | Async/await nativo, performance |
| **Bot Framework** | python-telegram-bot | 20+ | Async, bem mantido, docs completas |
| **HTTP Client** | httpx | latest | Async, HTTP/2, timeouts configuráveis |
| **Scheduler** | APScheduler | latest | Cron-like, in-process, robusto |
| **Database** | SQLite | 3.x | Zero-config, file-based, suficiente para uso |
| **ORM** | sqlite3 (stdlib) | - | Simplicidade (SQLAlchemy se crescer) |
| **Containerização** | Docker | latest | Portabilidade, Portainer-ready |
| **Orquestração** | Portainer Stack | - | Já configurado no VPS |
| **Reverse Proxy** | Traefik | - | Webhook futuro (TLS automático) |

### Decisões Arquiteturais (ADR)

#### ADR-001: Polling vs Webhook (MVP)
**Decisão**: Polling  
**Contexto**: MVP prioriza simplicidade; VPS já tem Traefik mas webhook exige configuração adicional  
**Consequências**:  
- ✅ Implementação mais simples
- ✅ Sem necessidade de TLS setup para MVP
- ✅ Mais robusto para reconexões
- ⚠️ Latência ligeiramente maior (~1-2s)
- 🔄 Migrar para webhook na Fase 2

#### ADR-002: SQLite vs PostgreSQL
**Decisão**: SQLite  
**Contexto**: Uso pessoal, estimativa < 10k registros/mês, VPS com recursos limitados  
**Consequências**:  
- ✅ Zero dependências externas
- ✅ Backup simples (copy file)
- ✅ Queries rápidas para escala esperada
- ⚠️ Não suporta concorrência write (ok para single-process bot)
- 🔄 Migrar para PostgreSQL se multi-instância

#### ADR-003: Mensagem Consolidada vs Individual
**Decisão**: Consolidada (1 mensagem com Top N)  
**Contexto**: Evitar flood no grupo Telegram (rate limits + UX)  
**Consequências**:  
- ✅ Reduz API calls do Telegram
- ✅ Melhor UX (1 scroll vs 10 mensagens)
- ✅ Facilita arquivamento/pesquisa
- ⚠️ Limite de 4096 chars por mensagem (Top 10-15 cabe tranquilo)

***

## 9) Modelo de Dados (SQLite)

### Diagrama ER

```
┌─────────────────┐       ┌─────────────────┐
│    settings     │       │  products_seen  │
├─────────────────┤       ├─────────────────┤
│ key (PK)        │       │ item_id (PK)    │
│ value           │       │ first_seen_at   │
└─────────────────┘       │ last_seen_at    │
                          │ last_price_min  │
                          │ last_discount   │
         ┌────────────────┤ last_commission │
         │                │ last_score      │
         │                │ raw_json        │
         │                └─────────────────┘
         │                         │
         │                         │
         ▼                         ▼
┌─────────────────┐       ┌──────────────────┐
│      links      │       │ sent_messages    │
├─────────────────┤       ├──────────────────┤
│ id (PK)         │       │ id (PK)          │
│ origin_url (UQ) │◄──────┤ item_id (FK)     │
│ short_link      │       │ group_id         │
│ sub_ids_json    │       │ short_link (FK)  │
│ created_at      │       │ sent_at          │
└─────────────────┘       │ batch_id         │
                          └──────────────────┘
         ▲                         
         │                         
         │                ┌─────────────────┐
         └────────────────┤      runs       │
                          ├─────────────────┤
                          │ id (PK)         │
                          │ run_type        │
                          │ started_at      │
                          │ ended_at        │
                          │ items_fetched   │
                          │ items_approved  │
                          │ items_sent      │
                          │ error_summary   │
                          └─────────────────┘
```

### Schema SQL

```sql
-- Configurações globais (JSON-based key-value)
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Produtos já vistos (histórico)
CREATE TABLE products_seen (
    item_id INTEGER PRIMARY KEY,
    first_seen_at DATETIME NOT NULL,
    last_seen_at DATETIME NOT NULL,
    last_price_min REAL,
    last_discount_rate INTEGER,
    last_commission REAL,
    last_commission_rate REAL,
    last_score REAL,
    raw_json TEXT  -- Opcional: payload completo da API
);
CREATE INDEX idx_products_seen_last_seen ON products_seen(last_seen_at);

-- Short links gerados (cache + auditoria)
CREATE TABLE links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    origin_url TEXT UNIQUE NOT NULL,
    short_link TEXT NOT NULL,
    sub_ids_json TEXT,  -- JSON array: ["tg", "grupo1", "curadoria", ...]
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_used_at DATETIME
);
CREATE INDEX idx_links_origin ON links(origin_url);
CREATE INDEX idx_links_created ON links(created_at);

-- Mensagens enviadas (deduplicação + rastreabilidade)
CREATE TABLE sent_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    group_id TEXT NOT NULL,
    short_link TEXT NOT NULL,
    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    batch_id TEXT,  -- Ex: "20260113_0800_curadoria"
    FOREIGN KEY (item_id) REFERENCES products_seen(item_id)
);
CREATE INDEX idx_sent_item_group ON sent_messages(item_id, group_id);
CREATE INDEX idx_sent_batch ON sent_messages(batch_id);

-- Execuções (logs estruturados)
CREATE TABLE runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_type TEXT NOT NULL,  -- "scheduled" | "manual"
    started_at DATETIME NOT NULL,
    ended_at DATETIME,
    items_fetched INTEGER DEFAULT 0,
    items_approved INTEGER DEFAULT 0,
    items_sent INTEGER DEFAULT 0,
    error_summary TEXT,
    success BOOLEAN DEFAULT 1
);
CREATE INDEX idx_runs_started ON runs(started_at DESC);
```

***

## 10) Integração Shopee Affiliate API

### Endpoint Base
```
https://open-api.affiliate.shopee.com.br/graphql
```

### Autenticação (SHA256 HMAC)

**Header**:
```
Authorization: SHA256 Credential={AppId}, Timestamp={Timestamp}, Signature={Signature}
```

**Cálculo da Signature**:
```python
import hashlib

def generate_signature(app_id: str, secret: str, timestamp: int, payload: str) -> str:
    """Gera assinatura SHA256 para Shopee API"""
    message = f"{app_id}{timestamp}{payload}{secret}"
    return hashlib.sha256(message.encode()).hexdigest()
```

**Validação de Timestamp**:
- Timestamp em segundos (Unix epoch)
- Tolerância: ±10 minutos
- Erro 401 se fora da janela

### Rate Limits
- **Limite global**: 2000 requests/hora
- **Estratégia de mitigação**:
  - Cache de short links (30 dias TTL)
  - Limit por execução: `max_pages * page_limit` (default: 5 * 50 = 250 itens)
  - Monitoramento contínuo via header `X-RateLimit-Remaining` (se disponível)

### Operação 1: productOfferV2

**Query GraphQL**:
```graphql
query ProductOfferV2($request: ProductSearchRequest!) {
  productOfferV2(request: $request) {
    nodes {
      itemId
      productName
      productLink
      originUrl
      priceMin
      priceMax
      priceDiscountRate
      commission
      commissionRate
      shopName
      sales
      rating
      imageUrl
    }
    pageInfo {
      page
      limit
      hasNextPage
    }
  }
}
```

**Variables**:
```json
{
  "request": {
    "keywords": ["fone bluetooth"],
    "productCatId": [11043380],
    "limit": 50,
    "page": 1,
    "listType": "hot"
  }
}
```

**Campos Retornados** (relevantes):
- `itemId` (int): ID único do produto
- `productName` (str): Nome
- `priceMin` (float): Preço mínimo (usar este para cálculos)
- `priceDiscountRate` (int): Desconto em % (0-100)
- `commission` (float): Comissão em R$
- `commissionRate` (float): Taxa de comissão (0.00-1.00)
- `originUrl` (str): URL para gerar short link

### Operação 2: generateShortLink

**Query GraphQL**:
```graphql
mutation GenerateShortLink($request: GenerateShortLinkRequest!) {
  generateShortLink(request: $request) {
    shortLink
    error {
      code
      message
    }
  }
}
```

**Variables**:
```json
{
  "request": {
    "originUrl": "https://shopee.com.br/product/123456/789012",
    "subIds": ["tg", "grupo1", "curadoria", "20260113_0800", "fonebluetooth"]
  }
}
```

**SubIds (limitações)**:
- Máximo 5 strings
- Cada string: max 255 chars
- Caracteres permitidos: alphanumeric + `_` + `-`

***

## 11) Fluxos de Operação Detalhados

### Fluxo 1: Curadoria Automática (Agendada)

```
┌─────────────────────────────────────────────────────────┐
│ 1) APScheduler dispara no horário configurado          │
└────────────────┬────────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 2) Carrega configurações (keywords, thresholds, etc)   │
│    └─ SELECT * FROM settings WHERE key IN (...)        │
└────────────────┬────────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 3) Loop por keywords/categorias                         │
│    └─ Para cada keyword:                                │
│       └─ productOfferV2(keyword, limit, page)          │
│          └─ Retry 3x com backoff se falhar             │
└────────────────┬────────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 4) Filtragem local                                      │
│    • commission >= 8.00 BRL                             │
│    • commissionRate >= 0.08                             │
│    • priceDiscountRate >= 15                            │
│    • priceMin <= price_max (se configurado)             │
│    • rating >= 4.7 (se disponível)                      │
└────────────────┬────────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 5) Rankeamento por score                                │
│    score = (commission * 1.0) + (discount * 0.5)        │
│             - (price * 0.02)                            │
│    └─ Sort DESC, pegar Top N                            │
└────────────────┬────────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 6) Deduplicação                                         │
│    └─ SELECT item_id FROM sent_messages                 │
│       WHERE item_id IN (...) AND sent_at > NOW() - 7d   │
│    └─ Remove duplicatas                                 │
└────────────────┬────────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 7) Geração de short links                               │
│    └─ Para cada produto:                                │
│       └─ Consulta cache: SELECT short_link FROM links   │
│          WHERE origin_url = ? AND created_at > NOW()-30d│
│       └─ Se não existe:                                 │
│          └─ generateShortLink(originUrl, subIds)        │
│          └─ INSERT INTO links                           │
└────────────────┬────────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 8) Formatação de mensagem consolidada                   │
│    └─ Render template HTML com Top N produtos          │
└────────────────┬────────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 9) Envio para grupo Telegram                            │
│    └─ bot.send_message(chat_id, text, parse_mode=HTML) │
│    └─ Retry 3x com backoff se falhar                    │
└────────────────┬────────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 10) Persistência                                        │
│     └─ INSERT INTO products_seen (upsert)               │
│     └─ INSERT INTO sent_messages (batch_id)             │
│     └─ INSERT INTO runs (summary)                       │
└────────────────┬────────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 11) Log estruturado                                     │
│     └─ {"level": "INFO", "fetched": 245, ...}           │
└─────────────────────────────────────────────────────────┘
```

### Fluxo 2: Conversão Manual

```
User: Clica "Converter Link"
   │
   ▼
Bot: "Envie o link Shopee" (Estado: AWAITING_LINK)
   │
   ▼
User: Envia URL
   │
   ▼
Bot: Validação (regex + domínio)
   │
   ├─ Inválida? → "❌ Link inválido"
   │
   └─ Válida? ▼
      │
      Normaliza URL (remove params desnecessários)
      │
      ▼
      Consulta cache (SELECT FROM links WHERE origin_url = ?)
      │
      ├─ Cache hit? → Retorna short_link cached
      │
      └─ Cache miss? ▼
         │
         generateShortLink(url, subIds=["tg","manual",timestamp])
         │
         ▼
         INSERT INTO links
         │
         ▼
         Retorna short_link + texto formatado
```

***

## 12) Critérios de Aceitação (MVP)

### Critério 1: Menu Funcional
- [ ] Comando `/start` exibe menu com 4 botões
- [ ] Apenas admin pode acionar (allowlist)
- [ ] Callbacks respondem corretamente
- [ ] Mensagens de não-admin são ignoradas silenciosamente

### Critério 2: Converter Link
- [ ] Botão "Converter Link" ativa modo listening
- [ ] Valida URL Shopee (domínios válidos)
- [ ] Gera short link via API com subIds padronizados
- [ ] Retorna mensagem formatada HTML com link
- [ ] Timeout de 60s se usuário não responder

### Critério 3: Curadoria Agora (Manual)
- [ ] Botão "Curadoria Agora" executa rotina completa
- [ ] Busca produtos, filtra, ranqueia
- [ ] Envia Top N no grupo (1 mensagem consolidada)
- [ ] Execução completa em < 60s (p95)

### Critério 4: Curadoria Automática (Agendada)
- [ ] APScheduler roda no intervalo configurado (default: 12h)
- [ ] Execução sem intervenção manual
- [ ] Logs estruturados de início/fim/contadores
- [ ] Deduplicação: zero duplicatas por período

### Critério 5: Persistência
- [ ] SQLite persiste em volume Docker `/data`
- [ ] Tabelas criadas automaticamente no primeiro boot
- [ ] Queries indexed (< 100ms p99)
- [ ] Backup manual: `docker cp container:/data/mariabico.db`

### Critério 6: Status
- [ ] Comando `/status` retorna dashboard completo
- [ ] Métricas corretas: última execução, contadores, rate limit
- [ ] Botão "Atualizar" recarrega dados

### Critério 7: Observabilidade
- [ ] Logs JSON no stdout (parseable pelo Portainer)
- [ ] Campos obrigatórios: timestamp, level, component, message
- [ ] Errors com stacktrace completo

### Critério 8: Deploy
- [ ] Container sobe via Portainer Stack
- [ ] Network `ProfRamosNet` configurada
- [ ] Secrets via environment variables (não hardcoded)
- [ ] Health check responde positivo

### Critério 9: Segurança
- [ ] Allowlist implementada (admin_id)
- [ ] Secrets nunca aparecem em logs
- [ ] Input sanitization em URLs

### Critério 10: Rate Limit
- [ ] Cache de short links funciona (evita chamadas duplicadas)
- [ ] Execução não excede 2000 req/h
- [ ] Retry com backoff em falhas transitórias

***

## 13) Deploy (Docker + Portainer + Traefik)

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements e instala deps Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código
COPY . .

# Cria diretório de dados
RUN mkdir -p /data

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os; exit(0 if os.path.exists('/data/mariabico.db') else 1)"

# Roda bot
CMD ["python", "-u", "main.py"]
```

### requirements.txt

```txt
python-telegram-bot>=20.0,<21.0
httpx>=0.27.0
apscheduler>=3.10.0
python-dotenv>=1.0.0
```

### Portainer Stack (docker-compose.yml)

```yaml
version: '3.8'

services:
  mariabicobot:
    image: gabrielramos/mariabicobot:latest
    container_name: mariabicobot
    restart: unless-stopped
    
    environment:
      # Telegram
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - ADMIN_TELEGRAM_USER_ID=${ADMIN_TELEGRAM_USER_ID}
      - TARGET_GROUP_ID=${TARGET_GROUP_ID}
      
      # Shopee
      - SHOPEE_APP_ID=${SHOPEE_APP_ID}
      - SHOPEE_SECRET=${SHOPEE_SECRET}
      
      # Config
      - TZ=America/Sao_Paulo
      - LOG_LEVEL=INFO
      - DB_PATH=/data/mariabico.db
      
      # Scheduler
      - SCHEDULE_CRON=0 */12 * * *
    
    volumes:
      - mariabicobot_/data
    
    networks:
      - ProfRamosNet
    
    labels:
      # Traefik (webhook futuro)
      - "traefik.enable=false"  # MVP usa polling
      # Para webhook na Fase 2:
      # - "traefik.enable=true"
      # - "traefik.http.routers.mariabicobot.rule=Host(`mariabicobot.proframos.com`) && PathPrefix(`/webhook`)"
      # - "traefik.http.routers.mariabicobot.tls=true"
      # - "traefik.http.routers.mariabicobot.tls.certresolver=letsencrypt"

networks:
  ProfRamosNet:
    external: true

volumes:
  mariabicobot_
    driver: local
```

### Environment Variables (.env no Portainer)

```bash
# Telegram
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_TELEGRAM_USER_ID=123456789
TARGET_GROUP_ID=-1001234567890

# Shopee
SHOPEE_APP_ID=1000000
SHOPEE_SECRET=abcdef1234567890abcdef1234567890

# Opcional (defaults no código)
SCHEDULE_CRON=0 */12 * * *
LOG_LEVEL=INFO
```

### Deploy Workflow

1. **Build local**:
```bash
docker build -t gabrielramos/mariabicobot:latest .
```

2. **Push para DockerHub**:
```bash
docker push gabrielramos/mariabicobot:latest
```

3. **Deploy via Portainer**:
   - Stacks → Add Stack → Name: `mariabicobot`
   - Copiar `docker-compose.yml`
   - Adicionar environment variables
   - Deploy

4. **Verificar logs**:
```bash
docker logs -f mariabicobot --tail 100
```

5. **Backup database**:
```bash
docker cp mariabicobot:/data/mariabico.db ./backup_$(date +%Y%m%d).db
```

***

## 14) Dependências e Pré-requisitos

| Dependência | Status | Ação Necessária | Responsável |
|-------------|--------|-----------------|-------------|
| **Shopee Affiliate API** | ✅ Obtido | Validar credenciais funcionam | Gabriel |
| **Token Bot Telegram** | 🟡 Pendente | Criar via @BotFather | Gabriel |
| **Grupo Privado Telegram** | 🟡 Pendente | Criar grupo + adicionar bot como admin | Gabriel |
| **VPS com Portainer** | ✅ Configurado | - | Gabriel |
| **Traefik no VPS** | ✅ Configurado | - (webhook Fase 2) | Gabriel |
| **Domínio mariabicobot.proframos.com** | ✅ Apontado | - (webhook Fase 2) | Gabriel |
| **DockerHub Account** | ✅ Existente | Criar repo `mariabicobot` | Gabriel |

***

## 15) Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| **Mudança na API Shopee** | Média | Alto | Monitorar changelog oficial; versionar queries GraphQL; testes automatizados |
| **Rate limit atingido** | Baixa | Médio | Cache de links (30d TTL); limitar pages/execução; alertar se > 90% usado |
| **Campos inconsistentes** | Média | Baixo | Fallbacks: `priceMin` → `price`; validar tipos; logs de warning |
| **Flood no grupo** | Baixa | Baixo | Mensagem consolidada (1 mensagem com Top N); máximo 15 itens por batch |
| **Perda de dados SQLite** | Baixa | Alto | Backup automático semanal via cron; volume Docker persistente |
| **Telegram Bot Token vazado** | Baixa | Crítico | Environment variables; `.env` no `.gitignore`; rotacionar se suspeita |
| **VPS offline** | Baixa | Médio | Monitoramento externo (UptimeRobot); restart automático do container |
| **Atribuição incorreta** | Média | Médio | SubIds padronizados; auditoria manual de conversões (Fase 2) |

***

## 16) Open Questions

| ID | Questão | Opções | Decisão | Data |
|----|---------|--------|---------|------|
| **OQ-01** | Frequência ideal de curadoria automática? | 6h / 12h / 24h | ⏳ Pendente | - |
| **OQ-02** | Tamanho do Top N para envio? | 10 / 20 / 30 | ⏳ Pendente | - |
| **OQ-03** | Período de deduplicação? | 7d / 14d / 30d | ⏳ Pendente | - |
| **OQ-04** | Formato da mensagem: Markdown ou HTML? | MarkdownV2 / HTML | ✅ HTML | 13/01 |
| **OQ-05** | Incluir imagem do produto na mensagem? | Sim / Não | ⏳ Pendente | - |
| **OQ-06** | Backup automático: frequência? | Diário / Semanal | ⏳ Pendente | - |
| **OQ-07** | Webhook na Fase 2: necessário? | Sim / Não | 🔄 Avaliar | - |

***

## 17) Timeline e Roadmap

### Fase 1 (MVP) — 2 semanas (27/01/2026)

**Semana 1: Core + Infraestrutura** (13/01 - 19/01)
- [x] PRD finalizado
- [ ] Setup projeto (repo, Docker, CI básico)
- [ ] Cliente Shopee API (auth + queries)
- [ ] Schema SQLite + migrations
- [ ] Bot Telegram básico (menu + handlers)
- [ ] Lógica de curadoria (fetch + filter + rank)

**Semana 2: Integração + Deploy** (20/01 - 27/01)
- [ ] Geração de short links + subIds
- [ ] Formatação de mensagens
- [ ] Deduplicação
- [ ] APScheduler integration
- [ ] Logs estruturados
- [ ] Testes manuais
- [ ] Deploy em Portainer
- [ ] Documentação operacional

### Fase 2 (Configuração Dinâmica) — 4 semanas (03/02 - 02/03)
- [ ] Comandos `/config` para editar keywords/thresholds
- [ ] Interface inline para ajustar pesos do score
- [ ] Integração com `conversionReport`
- [ ] Dashboard de performance por subId
- [ ] Webhook mode (Traefik + TLS)
- [ ] Multi-grupos

### Fase 3 (Analytics Avançado) — Backlog
- [ ] Feed público (JSON/HTML) para vitrine
- [ ] Relatórios automáticos semanais/mensais
- [ ] Predição de conversão via histórico
- [ ] Integração com Google Sheets
- [ ] Painel web administrativo

***

## 18) Glossário

| Termo | Definição |
|-------|-----------|
| **Affiliate Link** | Link rastreável que atribui conversões ao afiliado |
| **SubIds** | Identificadores customizados no link (até 5) para rastreamento granular |
| **Curadoria** | Processo de seleção automatizada de produtos por score |
| **Rate Limit** | Limite de requisições por hora (Shopee: 2000/h) |
| **Short Link** | URL encurtada gerada pela Shopee (`https://shope.ee/...`) |
| **InlineKeyboard** | Botões interativos no Telegram (abaixo da mensagem) |
| **Polling** | Método de receber updates do Telegram via long polling HTTP |
| **Webhook** | Método de receber updates via POST HTTP reverso |
| **TTL** | Time to Live - tempo de validade de um registro cached |
| **Deduplicação** | Evitar reenviar o mesmo produto em período definido |

***

## 19) Referências

- [Shopee Affiliate API Documentation](https://open.shopee.com/documents/v2/v2.affiliate.overview)
- [python-telegram-bot Documentation](https://docs.python-telegram-bot.org/)
- [APScheduler Documentation](https://apscheduler.readthedocs.io/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Portainer Documentation](https://docs.portainer.io/)

***

## 20) Aprovação

| Papel | Nome | Assinatura | Data |
|-------|------|------------|------|
| **Product Owner** | Gabriel Ramos | ⏳ Pendente | - |
| **Tech Lead** | Gabriel Ramos | ⏳ Pendente | - |
| **Desenvolvedor** | Gabriel Ramos | ⏳ Pendente | - |

***

**Versão**: 1.0  
**Status**: Aguardando aprovação para início do desenvolvimento  
**Última atualização**: 13/01/2026 14:30 BRT

Fontes
