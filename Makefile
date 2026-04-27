.PHONY: setup run-dev-agent run-analyst-agent ui test eval lint fmt clean

# ── Setup ────────────────────────────────────────────────────────────────────
setup:
	docker compose -f infra/docker-compose.yml up -d
	pip install -e ".[dev]"
	pre-commit install
	@echo "Ready. Run: make run-dev-agent SPEC=cases/dev_agent/examples/feature_health.md"

# ── Cases ────────────────────────────────────────────────────────────────────
run-dev-agent:
	@test -n "$(SPEC)" || (echo "Usage: make run-dev-agent SPEC=path/to/spec.md" && exit 1)
	python cases/dev_agent/main.py --spec $(SPEC)

run-analyst-agent:
	python cases/analyst_agent/main.py

# ── UI ───────────────────────────────────────────────────────────────────────
ui:
	chainlit run ui/chainlit_app.py --host 0.0.0.0 --port 8000

# ── Quality ──────────────────────────────────────────────────────────────────
test:
	pytest tests/ -v

eval:
	python agentkit/evaluation/harness.py

lint:
	ruff check .

fmt:
	ruff format .

# ── Cleanup ──────────────────────────────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	rm -rf out/ .pytest_cache/ .ruff_cache/ .mypy_cache/ htmlcov/ .coverage
