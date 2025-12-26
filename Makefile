COMPOSE_FILE ?= ops/docker/docker-compose.yml
UI_DIR ?= apps/ui
COMPOSE := docker compose -f $(COMPOSE_FILE)
PLK_ROOT ?= $(CURDIR)
PLK_PYTHON ?= $(PLK_ROOT)/.venv/bin/python

.PHONY: check-compose up infra ui down restart logs reset smoke demo

check-compose:
	@docker compose version >/dev/null 2>&1 || ( \
		echo "ERROR: Docker Compose v2 is required (docker compose ...). docker-compose v1 is not supported."; \
		echo "Please install Docker Desktop or the Compose v2 plugin."; \
		exit 1 )

up: infra
	cd $(UI_DIR) && (test -d node_modules || npm install) && npm run dev

infra: check-compose
	$(COMPOSE) up -d

ui:
	cd $(UI_DIR) && npm run dev

down:
	$(COMPOSE) down

restart: down infra

logs:
	$(COMPOSE) logs -f

reset:
	$(COMPOSE) down -v

smoke:
	@PLK_ROOT=$(PLK_ROOT) PYTHONPATH=$(PLK_ROOT) $(PLK_PYTHON) tools/smoke.py

demo:
	@PLK_ROOT=$(PLK_ROOT) PYTHONPATH=$(PLK_ROOT) $(PLK_PYTHON) tools/demo.py
