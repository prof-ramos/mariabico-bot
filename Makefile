# Makefile para orquestração de testes do MariaBicoBot
# Executa testes com diferentes estratégias de paralelização e filtragem

.PHONY: help test test-smoke test-unit test-integration test-all test-coverage
.PHONY: test-parallel test-sharded lint lint-fix format check
.PHONY: clean clean-pyc clean-build clean-test install dev-install

# Variáveis
PYTHON := python
PIP := pip
PYTEST := pytest
PYTEST_OPTIONS := -v --tb=short --asyncio-mode=auto
SOURCE_DIRS := src
TEST_DIRS := tests

# ============================================================================
# HELP
# ============================================================================
help: ## Mostra este help
	@echo "Uso: make [target]"
	@echo ""
	@echo "Targets disponíveis:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

# ============================================================================
# INSTALAÇÃO
# ============================================================================
install: ## Instala dependências de produção
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

dev-install: ## Instala dependências de desenvolvimento
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

# ============================================================================
# TESTES - ESTRATÉGIAS DE ORQUESTRAÇÃO
# ============================================================================

# Testes rápidos de smoke (críticos)
test-smoke: ## Executa apenas smoke tests (críticos)
	$(PYTEST) -m smoke $(PYTEST_OPTIONS)

# Testes unitários (isolados, rápidos)
test-unit: ## Executa testes unitários
	$(PYTEST) -m "unit and not slow" $(PYTEST_OPTIONS) --cov=src --cov-report=term-missing

# Testes de integração (sem API real)
test-integration: ## Executa testes de integração (sem API real)
	$(PYTEST) -m "integration and not shopee_api and not slow" $(PYTEST_OPTIONS)

# Testes completos
test-all: ## Executa todos os testes (exceto API real)
	$(PYTEST) -m "not shopee_api and not slow" $(PYTEST_OPTIONS) --cov=src --cov-report=html

# Testes com API Shopee real
test-api: ## Executa testes com API Shopee real (requer .env)
	$(PYTEST) -m shopee_api $(PYTEST_OPTIONS)

# ============================================================================
# PARALELIZAÇÃO E OTIMIZAÇÃO
# ============================================================================

# Execução paralela automática
test-parallel: ## Executa testes em paralelo (todos os CPUs)
	$(PYTEST) -m "not shopee_api and not slow" -n auto $(PYTEST_OPTIONS)

# Execução shardada (divide testes em N grupos)
test-sharded: ## Executa testes divididos em shards (requer pytest-xdist)
	$(PYTEST) -m "not shopee_api and not slow" -n 4 --dist=loadscope $(PYTEST_OPTIONS)

# Execução com análise de cobertura
test-coverage: ## Executa testes com relatório de cobertura
	$(PYTEST) -m "not shopee_api and not slow" \
		--cov=src \
		--cov-report=html:htmlcov \
		--cov-report=term-missing:skip-covered \
		--cov-report=xml:coverage.xml \
		--cov-fail-under=70 \
		$(PYTEST_OPTIONS)

# Execução por velocidade (mais lentos primeiro)
test-slow-first: ## Executa testes lentos primeiro
	$(PYTEST) -m "not shopee_api" --durations=0 -v $(PYTEST_OPTIONS)

# ============================================================================
# LINT E FORMATAÇÃO
# ============================================================================

lint: ## Executa linters (ruff, mypy)
	ruff check $(SOURCE_DIRS) $(TEST_DIRS)
	ruff format --check $(SOURCE_DIRS) $(TEST_DIRS)
	mypy src/

lint-fix: ## Corrige problemas de lint automaticamente
	ruff check --fix $(SOURCE_DIRS) $(TEST_DIRS)
	ruff format $(SOURCE_DIRS) $(TEST_DIRS)

format: ## Formata código com ruff
	ruff format $(SOURCE_DIRS) $(TEST_DIRS)

check: lint test-unit ## Executa lint + testes unitários

# ============================================================================
# LIMPEZA
# ============================================================================
clean: clean-pyc clean-build clean-test ## Limpa todos os artefatos

clean-pyc: ## Remove arquivos .pyc e __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true

clean-build: ## Remove artefatos de build
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml

clean-test: ## Remove artefatos de testes
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf coverage.json
	rm -rf smoke-report.json

# ============================================================================
# RELATÓRIOS
# ============================================================================
report-coverage: ## Abre relatório de cobertura no navegador
	$(PYTHON) -m webbrowser htmlcov/index.html || true

report-json: ## Gera relatório JSON dos testes
	$(PYTEST) -m "not shopee_api" \
		--json-report \
		--json-report-file=test-report.json \
		$(PYTEST_OPTIONS)

# ============================================================================
# CI/CD LOCAL
# ============================================================================
ci-local: ## Simula pipeline CI/CD localmente
	@echo "=== FASE 1: Smoke Tests ==="
	$(MAKE) test-smoke
	@echo ""
	@echo "=== FASE 2: Unit Tests ==="
	$(MAKE) test-unit
	@echo ""
	@echo "=== FASE 3: Integration Tests ==="
	$(MAKE) test-integration
	@echo ""
	@echo "=== FASE 4: Coverage ==="
	$(MAKE) test-coverage
	@echo ""
	@echo "=== Pipeline CI Local concluído com sucesso! ==="

# ============================================================================
# DOCKER
# ============================================================================
docker-test: ## Executa testes dentro do container Docker
	docker build -t mariabicobot-test .
	docker run --rm \
		-v $(PWD)/tests:/app/tests \
		mariabicobot-test \
		pytest -m "not shopee_api" -v

# ============================================================================
# DESENVOLVIMENTO
# ============================================================================
dev: ## Inicia modo desenvolvimento com hot reload
	$(PYTHON) -m src.main

watch: ## Observa mudanças e roda testes automaticamente (requer pytest-watch)
	$(PIP) install pytest-watch
	ptw -- $(PYTEST_OPTIONS) -x

# ============================================================================
# UTILITÁRIOS
# ============================================================================
count-tests: ## Conta total de testes
	@echo "Total de testes:"
	@$(PYTEST) --collect-only -q | grep "test session starts" -A 100 | tail -n 1 | awk '{print $$3}'

list-slow: ## Lista testes marcados como lentos
	@$(PYTEST) --collect-only -m slow -q | grep test_

list-smoke: ## Lista testes de smoke
	@$(PYTEST) --collect-only -m smoke -q | grep test_
