SHELL := /bin/bash
.DEFAULT_GOAL := help

BACKEND_DIR := backend
FRONTEND_DIR := frontend

.PHONY: help install install-backend install-frontend seed backend frontend dev eval build-frontend stop clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: install-backend install-frontend ## Install backend (uv) and frontend (npm) dependencies

install-backend: ## Install backend dependencies with uv
	cd $(BACKEND_DIR) && uv sync

install-frontend: ## Install frontend dependencies with npm
	cd $(FRONTEND_DIR) && npm install

seed: ## Create/reset the local SQLite inventory database
	cd $(BACKEND_DIR) && uv run python -m app.db.seed

backend: ## Run the FastAPI backend with reload on http://localhost:8000
	cd $(BACKEND_DIR) && uv run uvicorn app.main:app --reload --port 8000

frontend: ## Run the Vite dev server on http://localhost:5173
	cd $(FRONTEND_DIR) && npm run dev

dev: ## Run backend + frontend together (Ctrl-C stops both)
	@trap 'kill 0' EXIT INT TERM; \
	$(MAKE) backend & \
	$(MAKE) frontend & \
	wait

eval: ## Run the NL->SQL validation dataset against the live pipeline
	cd $(BACKEND_DIR) && uv run python -m app.eval.runner

build-frontend: ## Type-check and build the frontend for production
	cd $(FRONTEND_DIR) && npm run build

stop: ## Kill any backend/frontend dev servers left running on :8000 / :5173
	@lsof -ti:8000 | xargs kill 2>/dev/null || true
	@lsof -ti:5173 | xargs kill 2>/dev/null || true
	@echo "Stopped any processes on :8000 (backend) and :5173 (frontend)."

clean: stop ## Stop dev servers, then remove virtualenvs, node_modules, build output, and local data
	rm -rf $(BACKEND_DIR)/.venv $(BACKEND_DIR)/data/store_inventory.db $(BACKEND_DIR)/data/chroma
	rm -rf $(FRONTEND_DIR)/node_modules $(FRONTEND_DIR)/dist
