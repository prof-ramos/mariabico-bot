# Estratégia de Testes - MariaBicoBot

## Visão Geral

Este projeto implementa uma estratégia de testes abrangente com orquestração inteligente, classificação automática e execução otimizada.

## Estrutura de Testes

```
tests/
├── conftest.py              # Configuração centralizada + fixtures
├── fixtures/                # Fixtures específicas (quando necessário)
├── unit/                    # Testes unitários (rápidos, isolados)
│   ├── test_scoring.py      # Testes de algoritmo de score
│   ├── test_link_gen.py     # Testes de geração de links
│   ├── test_auth.py         # Testes de autenticação Shopee
│   └── test_deduplicator.py # Testes de deduplicação
└── integration/             # Testes de integração (recursos externos)
    ├── test_shopee_api.py   # Testes de API Shopee (mock + real)
    ├── test_curator.py      # Testes do fluxo de curadoria
    └── test_telegram_handlers.py # Testes de handlers Telegram
```

## Marcadores (Markers)

Os testes são categorizados usando marcadores pytest:

| Marcador | Descrição | Tempo Típico | Execução |
|----------|-----------|--------------|----------|
| `smoke` | Testes críticos que sempre devem passar | < 1s | Primeiro |
| `unit` | Testes unitários isolados | < 5s | Paralelo |
| `integration` | Testes com recursos externos | 5-30s | Sequencial |
| `shopee_api` | Testes que chamam API Shopee real | 10-60s | Opcional |
| `telegram` | Testes relacionados ao Telegram | < 10s | Paralelo |
| `database` | Testes que acessam banco | < 5s | Paralelo |
| `slow` | Testes lentos (executar separadamente) | > 30s | Manual |

## Comandos de Execução

### Execução Local

```bash
# Instalar dependências de desenvolvimento
make dev-install

# Executar smoke tests (críticos)
make test-smoke

# Executar testes unitários
make test-unit

# Executar testes de integração (sem API real)
make test-integration

# Executar todos os testes (exceto API real)
make test-all

# Executar com relatório de cobertura
make test-coverage

# Executar em paralelo (todos os CPUs)
make test-parallel

# Simular pipeline CI/CD localmente
make ci-local
```

### Execução Avançada

```bash
# Apenas testes de uma classe específica
pytest tests/unit/test_scoring.py::TestCalculateScore -v

# Apenas um teste específico
pytest tests/unit/test_scoring.py::TestCalculateScore::test_calculate_score_basic -v

# Testes que contenham "commission" no nome
pytest -k commission -v

# Testes excluindo os lentos
pytest -m "not slow" -v

# Paralelo com 4 workers
pytest -n 4 --dist=loadscope -v

# Re-executar apenas testes que falharam
pytest --lf -v

# Parar no primeiro fracasso
pytest -x -v

# Executar 3 vezes para detectar flakiness
pytest --count=3 -v
```

## Orquestração Inteligente

### Classificação Automática

O `conftest.py` implementa um classificador que:

1. **Ordena testes por criticidade**: Smoke > Unitários > Lentos
2. **Identifica dependências**: Testes que requerem APIs externas
3. **Categoriza por tipo**: Unitário, Integração, Smoke

### Estratégias de Execução

#### 1. Pipeline em Fases

```bash
# FASE 1: Smoke (críticos)
pytest -m smoke -v

# FASE 2: Unitários (paralelo)
pytest -m "unit and not slow" -n auto --cov

# FASE 3: Integração
pytest -m "integration and not shopee_api" -v

# FASE 4: API real (opcional)
pytest -m shopee_api -v
```

#### 2. Execução Shardada

Divide testes em N grupos para execução paralela:

```bash
pytest -n 4 --dist=loadscope -v
```

#### 3. Execução por Velocidade

Testes mais lentos executam primeiro para maximizar utilização de CPU:

```bash
pytest --durations=0 -v
```

## CI/CD Pipeline

O pipeline `.github/workflows/tests.yml` implementa:

1. **Smoke Tests** (5 min timeout) - Executa primeiro, falha rápido se problemas críticos
2. **Unit Tests** (10 min timeout) - Paralelizado em 2 shards
3. **Integration Tests** (15 min timeout) - Sem API real
4. **Coverage** - Combina relatórios, falha se < 70%
5. **Security Scan** - Bandit + Safety
6. **Docker Build** - Testa build da imagem

### Gatilhos

- Push para `main`/`develop`
- Pull requests
- Manual (workflow_dispatch com seleção de tipo)

## Fixtures Disponíveis

### Fixtures Gerais

```python
def temp_db_path() -> str  # Banco SQLite temporário
def db() -> Database       # Instância de Database
def db_conn() -> Connection  # Conexão bruta SQLite
```

### Fixtures Shopee

```python
def mock_shopee_client()       # Cliente Shopee mockado
def mock_shopee_response()     # Resposta padrão da API
def mock_shopee_response_product()  # Produto mockado
```

### Fixtures Configuração

```python
def mock_settings()            # Settings mockados
def reset_settings()           # Reseta singleton
```

### Fixtures Curator

```python
def curator()                  # Instância de Curator
def sample_product()           # Produto exemplo
def sample_products()          # Lista de produtos
```

### Fixtures Telegram

```python
def mock_telegram_update()     # Update mockado
def mock_telegram_context()    # Contexto mockado
```

## Escrevendo Novos Testes

### Teste Unitário

```python
import pytest

class TestMyFeature:
    """Testes para MyFeature."""

    @pytest.mark.smoke
    @pytest.mark.unit
    def test_critical_function(self):
        """Testa função crítica."""
        result = my_function(1, 2)
        assert result == 3

    @pytest.mark.unit
    def test_edge_case(self):
        """Testa caso de borda."""
        result = my_function(0, 0)
        assert result == 0
```

### Teste de Integração

```python
import pytest

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_flow(curator):
    """Testa fluxo completo."""
    result = await curator.curate(["keyword"])
    assert result["fetched"] > 0
```

### Teste com API Real

```python
@pytest.mark.slow
@pytest.mark.shopee_api
@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_api(real_client):
    """Testa com API Shopee real."""
    products = await real_client.search_products(["test"])
    assert len(products) > 0
```

## Cobertura

### Objetivos

- **Cobertura mínima**: 70%
- **Cobertura alvo**: 85%
- **Arquivos críticos**: 90%+

### Relatórios

```bash
# Gerar HTML
make test-coverage

# Abrir no navegador
make report-coverage

# JSON para CI
pytest --cov-report=json:coverage.json
```

## Troubleshooting

### Teste falha isoladamente mas passa no suite

```bash
# Detecta testes com efeitos colaterais
pytest --forcexit -v
```

### Teste assíncrono falha

```bash
# Verifica se async mode está configurado
pytest --asyncio-mode=auto -v
```

### Fixture não disponível

```bash
# Lista fixtures disponíveis
pytest --fixtures
```

### Paralelização causa conflitos

```bash
# Usa loadscope para isolar por escopo
pytest -n auto --dist=loadscope -v
```

## Boas Práticas

1. **Use marcadores apropriados**: Marque todos os testes com `unit`, `integration`, etc.
2. **Testes unitários devem ser rápidos**: < 5 segundos cada
3. **Mock dependências externas**: Use mocks para APIs, bancos, etc.
4. **Testes isolados**: Cada teste deve ser independente
5. **Nomes descritivos**: `test_[oque]_[quando]_[entao]`
6. **Um assert por teste**: Exceto para testes de smoke
7. **Use fixtures**: Evite duplicação de setup
8. **Documente testes complexos**: Adicione docstrings explicativas

## Monitoramento

### Métricas Coletadas

- Tempo de execução por teste
- Taxa de sucesso/falha
- Cobertura de código
- Testes flaky (que falham intermitentemente)

### Relatórios

- Smoke tests: Sempre visíveis no console
- Cobertura: HTML + JSON
- CI/CD: Resumo no PR (comentário)
- Performance: Top 10 testes mais lentos
