# Implementation Plan

Correções múltiplas no projeto MariaBicoBot envolvendo documentação, código Python e testes para melhorar robustez, portabilidade e consistência.

Esta implementação aborda 15 problemas distintos distribuídos entre arquivos de documentação, código fonte e testes. As correções incluem atualização de documentação para Windows, remoção de caminhos absolutos, implementação de paginação em APIs, tratamento robusto de dados, padronização de imports e melhorias em testes.

[Types]

Nenhuma alteração no sistema de tipos (dataclasses, tipos Python existentes permanecem inalterados).

[Files]

**Arquivos de Documentação:**
- `DEVELOPER_GUIDE.md`: Adicionar instruções de ativação do ambiente virtual para Windows (PowerShell e Command Prompt) após instruções macOS/Linux
- `implementation_plan.md`: Substituir todos os caminhos absolutos `file:///Users/gabrielramos/...` por caminhos relativos como `./src/shopee/auth.py` ou `src/shopee/auth.py`
- `TEST_ORCHESTRATION_SUMMARY.md`: Reformatar lista única compacta em lista vertical com bullets para melhor legibilidade

**Arquivos de Código Fonte - Handlers:**
- `src/bot/handlers.py`: Múltiplas correções
  - Remover `async` de `is_authorized()` (linha ~32)
  - Atualizar todas as chamadas para remover `await is_authorized(...)`
  - Substituir aritmética de timestamp por `timedelta` (linhas ~410-416)
  - Implementar paginação em `get_conversion_report()` ou aumentar limit para 500 (linhas ~419-426)
  - Adicionar parsing robusto para `commissionAmount` e normalizar status com conjunto (linhas ~435-446)

**Arquivos de Código Fonte - Core:**
- `src/bot/formatters.py`: Adicionar coerção defensiva de valores None/falsy para defaults em `format_report_message()` (linhas ~152-179)
- `src/bot/keyboards.py`: Verificar e remover caminhos absolutos se presentes
- `src/core/curator.py`: Traduzir comentário "# Handle rating" para português "# Tratar avaliação" (linha ~78)
- `src/core/scoring.py`: Verificar e remover caminhos absolutos se presentes
- `src/main.py`: Uniformizar formatação de `CallbackQueryHandler` registrations (linhas ~205-215)

**Arquivos de Código Fonte - Shopee:**
- `src/shopee/auth.py`: Verificar e remover caminhos absolutos se presentes
- `src/shopee/client.py`: Padronizar imports (reverter para relativos ou manter absolutos consistentemente) (linhas ~8-9)
- `src/shopee/queries.py`: Verificar e remover caminhos absolutos se presentes

**Arquivos de Testes:**
- `tests/conftest.py`: Remover atributo privado `update._effective_user` e usar apenas `update.effective_user` público (linhas ~291-295)
- `tests/integration/test_curator.py`: Substituir lista hardcoded `["keyword1", "keyword2", "keyword3"]` por variável `keywords` (linhas ~55-56, ~76-79)
- `tests/integration/test_shopee_api.py`: Múltiplas correções
  - Mudar `pytest.skip` para `pytest.xfail` com mensagem clara para exceções de API (linha ~171-177)
  - Capturar exceção GraphQL específica em vez de `Exception` genérica (linhas ~143-152)
  - Substituir `asyncio.run(client.close())` por `await client.close()` em fixture async (linhas ~133-135)
- `tests/integration/test_telegram_handlers.py`: Remover comentários de desenvolvimento (linhas ~293-297)

[Functions]

**Novas Funções:**
- Nenhuma nova função será criada (apenas modificações em existentes)

**Funções Modificadas:**
- `is_authorized()` em `src/bot/handlers.py`: Remover `async`, manter mesma assinatura e lógica
- `_generate_report()` em `src/bot/handlers.py`: Adicionar paginação ou aumentar limit para 500
- `format_report_message()` em `src/bot/formatters.py`: Adicionar coerção defensiva de None/falsy

**Funções Removidas:**
- Nenhuma função será removida

[Classes]

Nenhuma alteração em classes existentes. Apenas modificações em métodos internos de `ShopeeClient` se necessário para paginação.

[Dependencies]

Nenhuma nova dependência será adicionada. As correções usam apenas bibliotecas já presentes (pytest, pathlib, datetime, etc).

[Testing]

**Validação de Testes:**
- Executar `uv run pytest -m "not shopee_api"` para validar testes sem API real
- Executar `uv run pytest tests/unit/` para testes unitários específicos
- Verificar que todos os testes marcados como `smoke` passam

**Testes Modificados:**
- `tests/conftest.py`: Atualizar fixture `mock_telegram_update` para usar atributo público
- `tests/integration/test_curator.py`: Usar variável `keywords` consistente
- `tests/integration/test_shopee_api.py`: Melhorar tratamento de exceções e cleanup
- `tests/integration/test_telegram_handlers.py`: Limpar comentários de desenvolvimento

[Implementation Order]

1. **Correções de Documentação** (prioridade alta, sem dependências)
   - Atualizar `DEVELOPER_GUIDE.md` com instruções Windows
   - Remover caminhos absolutos de `implementation_plan.md`
   - Reformatar lista em `TEST_ORCHESTRATION_SUMMARY.md`

2. **Padronização de Imports** (afeta múltiplos arquivos)
   - Reverter imports em `src/shopee/client.py` para relativos
   - Verificar e remover caminhos absolutos dos demais arquivos

3. **Correções em Handlers** (bloco principal de lógica)
   - Remover `async` de `is_authorized()`
   - Atualizar todas as chamadas para remover `await`
   - Substituir aritmética de timestamp por `timedelta`
   - Implementar paginação em `get_conversion_report()`
   - Adicionar parsing robusto de comissão e status

4. **Correções em Formatters e Core**
   - Adicionar coerção defensiva em `format_report_message()`
   - Traduzir comentário em `src/core/curator.py`
   - Uniformizar formatação de handlers em `src/main.py`

5. **Correções em Testes**
   - Atualizar fixture em `tests/conftest.py`
   - Corrigir uso de variáveis em `tests/integration/test_curator.py`
   - Melhorar tratamento de exceções em `tests/integration/test_shopee_api.py`
   - Limpar comentários em `tests/integration/test_telegram_handlers.py`