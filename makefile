# Myrtus Monitor - Makefile
# Python project with uv package manager, Docker, Kubernetes, and Helm

.PHONY: help install install-dev clean lint format test test-unit test-collectors \
        test-monitor build docker-build docker-push helm-lint helm-template \
        helm-install helm-upgrade helm-uninstall run-node run-cluster run-node-example \
        run-cluster-example docker-run-node docker-run-cluster docker-run-node-example \
        docker-run-cluster-example dev-setup check-deps security-check all \
        update-deps update-git-deps \
        kind-setup kind-teardown kind-install kind-test-helm-value kind-test-label-override kind-test-all kind-apply-label-override kind-demo

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON_VERSION := 3.10
PROJECT_NAME := myrtus-monitor
DOCKER_IMAGE := ghcr.io/arubakube/myrtus-monitor
DOCKER_TAG ?= latest
HELM_CHART := charts/myrtus-monitor
NAMESPACE := myrtus-system

# Load local environment variables (e.g. GITLAB_TOKEN)
-include .env
export GITLAB_TOKEN

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
ORANGE := \033[38;5;208m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Myrtus Monitor - Available Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ { printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# Development Environment
dev-setup: ## Set up development environment
	@echo "$(BLUE)Setting up development environment...$(NC)"
	@command -v uv >/dev/null 2>&1 || { echo "$(RED)uv is required but not installed. Please install uv first.$(NC)"; exit 1; }
	uv sync --dev
	@echo "$(GREEN)Development environment ready!$(NC)"

install: ## Install production dependencies
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	uv sync --no-dev

install-dev: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	uv sync --dev

# Code Quality
lint: ## Run linting (ruff + pylint)
	@echo "$(BLUE)Running linting...$(NC)"
	uv run ruff check .
	uv run pylint monitor/

lint-fix: ## Run linting with auto-fixes
	@echo "$(BLUE)Running linting with auto-fixes...$(NC)"
	uv run ruff check --fix .
	@echo "$(YELLOW)Note: pylint issues need manual fixing$(NC)"

format: ## Format code with ruff
	@echo "$(BLUE)Formatting code...$(NC)"
	uv run ruff format .
	uv run ruff check --fix .

format-check: ## Check code formatting
	@echo "$(BLUE)Checking code formatting...$(NC)"
	uv run ruff format --check .

# Testing
test: ## Run all tests
	@echo "$(BLUE)Running all tests...$(NC)"
	uv run pytest tests/ -v

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	uv run pytest tests/unit/ -v

test-collectors: ## Run collector tests
	@echo "$(BLUE)Running collector tests...$(NC)"
	uv run pytest tests/ -m collectors -v

test-monitor: ## Run monitor tests
	@echo "$(BLUE)Running monitor tests...$(NC)"
	uv run pytest tests/ -m monitor -v

test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	uv run pytest tests/ --cov=monitor --cov-report=html --cov-report=term

# Security
security-check: ## Run security checks
	@echo "$(BLUE)Running security checks...$(NC)"
	uv run ruff check --select=S --exclude=tests .

# Build and Package
build: ## Build the package
	@echo "$(BLUE)Building package...$(NC)"
	uv build

clean: ## Clean build artifacts and cache
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Docker
docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -f docker/Dockerfile --build-arg GITLAB_TOKEN=$(GITLAB_TOKEN) -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

docker-push: docker-build ## Build and push Docker image
	@echo "$(BLUE)Pushing Docker image...$(NC)"
	docker push $(DOCKER_IMAGE):$(DOCKER_TAG)

docker-run-node: ## Run node monitor in Docker (requires NODE_NAME, NODE_TYPE, CLUSTER_ID, KB_ENDPOINT)
	@echo "$(BLUE)Running node monitor in Docker...$(NC)"
	@if [ -z "$(NODE_NAME)" ] || [ -z "$(NODE_TYPE)" ] || [ -z "$(CLUSTER_ID)" ] || [ -z "$(KB_ENDPOINT)" ]; then \
		echo "$(RED)Error: Required variables not set$(NC)"; \
		echo "Usage: make docker-run-node NODE_NAME=my-node NODE_TYPE=cloud CLUSTER_ID=my-cluster KB_ENDPOINT=http://kb:8080"; \
		exit 1; \
	fi
	docker run --rm -it --privileged --pid=host --network=host \
		-v /proc:/host/proc:ro \
		-v /sys:/host/sys:ro \
		-v /:/rootfs:ro \
		$(DOCKER_IMAGE):$(DOCKER_TAG) node-monitor \
		--node-name $(NODE_NAME) \
		--node-type $(NODE_TYPE) \
		--liqo-cluster-id $(CLUSTER_ID) \
		--kb-endpoint $(KB_ENDPOINT)

docker-run-cluster: ## Run cluster monitor in Docker (requires CLUSTER_ID, KB_ENDPOINT)
	@echo "$(BLUE)Running cluster monitor in Docker...$(NC)"
	@if [ -z "$(CLUSTER_ID)" ] || [ -z "$(KB_ENDPOINT)" ]; then \
		echo "$(RED)Error: Required variables not set$(NC)"; \
		echo "Usage: make docker-run-cluster CLUSTER_ID=my-cluster KB_ENDPOINT=http://kb:8080"; \
		exit 1; \
	fi
	docker run --rm -it \
		-v ~/.kube:/root/.kube:ro \
		$(DOCKER_IMAGE):$(DOCKER_TAG) cluster-monitor \
		--liqo-cluster-id $(CLUSTER_ID) \
		--kb-endpoint $(KB_ENDPOINT)

docker-run-node-example: ## Run node monitor with example parameters
	@echo "$(BLUE)Running node monitor with example parameters...$(NC)"
	docker run --rm -it --privileged --pid=host --network=host \
		-v /proc:/host/proc:ro \
		-v /sys:/host/sys:ro \
		-v /:/rootfs:ro \
		$(DOCKER_IMAGE):$(DOCKER_TAG) node-monitor \
		--node-name example-node \
		--node-type cloud \
		--skip-node-type-inference \
		--liqo-cluster-id example-cluster \
		--kb-endpoint http://localhost:8080 \
		--kb-disabled \
		--log-level DEBUG

docker-run-cluster-example: ## Run cluster monitor with example parameters
	@echo "$(BLUE)Running cluster monitor with example parameters...$(NC)"
	docker run --rm -it \
		-v ~/.kube:/root/.kube:ro \
		$(DOCKER_IMAGE):$(DOCKER_TAG) cluster-monitor \
		--liqo-cluster-id example-cluster \
		--kb-endpoint http://localhost:8080 \
		--kb-disabled \
		--log-level DEBUG

# Helm
helm-lint: ## Lint Helm chart
	@echo "$(BLUE)Linting Helm chart...$(NC)"
	helm lint $(HELM_CHART)

helm-template: ## Generate Kubernetes manifests from Helm chart
	@echo "$(BLUE)Generating Kubernetes manifests...$(NC)"
	helm template $(PROJECT_NAME) $(HELM_CHART) --namespace $(NAMESPACE)

helm-install: ## Install Helm chart
	@echo "$(BLUE)Installing Helm chart...$(NC)"
	helm install $(PROJECT_NAME) $(HELM_CHART) --namespace $(NAMESPACE) --create-namespace

helm-upgrade: ## Upgrade Helm chart
	@echo "$(BLUE)Upgrading Helm chart...$(NC)"
	helm upgrade $(PROJECT_NAME) $(HELM_CHART) --namespace $(NAMESPACE)

helm-uninstall: ## Uninstall Helm chart
	@echo "$(BLUE)Uninstalling Helm chart...$(NC)"
	helm uninstall $(PROJECT_NAME) --namespace $(NAMESPACE)

# Local Development
run-node: ## Run node monitor locally (requires NODE_NAME, NODE_TYPE, CLUSTER_ID, KB_ENDPOINT)
	@echo "$(BLUE)Running node monitor...$(NC)"
	@if [ -z "$(NODE_NAME)" ] || [ -z "$(NODE_TYPE)" ] || [ -z "$(CLUSTER_ID)" ] || [ -z "$(KB_ENDPOINT)" ]; then \
		echo "$(RED)Error: Required variables not set$(NC)"; \
		echo "Usage: make run-node NODE_NAME=my-node NODE_TYPE=cloud CLUSTER_ID=my-cluster KB_ENDPOINT=http://kb:8080"; \
		exit 1; \
	fi
	uv run node-monitor --node-name $(NODE_NAME) --node-type $(NODE_TYPE) --liqo-cluster-id $(CLUSTER_ID) --kb-endpoint $(KB_ENDPOINT)

run-cluster: ## Run cluster monitor locally (requires CLUSTER_ID, KB_ENDPOINT)
	@echo "$(BLUE)Running cluster monitor...$(NC)"
	@if [ -z "$(CLUSTER_ID)" ] || [ -z "$(KB_ENDPOINT)" ]; then \
		echo "$(RED)Error: Required variables not set$(NC)"; \
		echo "Usage: make run-cluster CLUSTER_ID=my-cluster KB_ENDPOINT=http://kb:8080"; \
		exit 1; \
	fi
	uv run cluster-monitor --liqo-cluster-id $(CLUSTER_ID) --kb-endpoint $(KB_ENDPOINT)

run-node-example: ## Run node monitor locally with example parameters
	@echo "$(BLUE)Running node monitor with example parameters...$(NC)"
	uv run node-monitor \
		--node-name $$(hostname) \
		--node-type cloud \
		--skip-node-type-inference \
		--liqo-cluster-id example-cluster \
		--kb-endpoint http://localhost:8080 \
		--kb-disabled \
		--log-level DEBUG

run-cluster-example: ## Run cluster monitor locally with example parameters
	@echo "$(BLUE)Running cluster monitor with example parameters...$(NC)"
	uv run cluster-monitor \
		--liqo-cluster-id example-cluster \
		--kb-endpoint http://localhost:8080 \
		--kb-disabled \
		--log-level DEBUG

# Dependency Management
check-deps: ## Check for dependency updates
	@echo "$(BLUE)Checking for dependency updates...$(NC)"
	uv tree
	@echo "$(YELLOW)Run 'uv sync --upgrade' to update dependencies$(NC)"

update-deps: ## Update dependencies
	@echo "$(BLUE)Updating dependencies...$(NC)"
	uv sync --upgrade

update-git-deps: ## Update git-sourced dependencies (e.g. mirtolib)
	@if [ -z "$(GITLAB_TOKEN)" ]; then \
		echo "$(RED)Error: GITLAB_TOKEN is not set.$(NC)"; \
		echo "Create a .env file in the project root with at least:"; \
		echo "  GITLAB_TOKEN=<your_gitlab_personal_access_token>"; \
		exit 1; \
	fi
	@echo "$(BLUE)Updating git-sourced dependencies...$(NC)"
	@cp pyproject.toml pyproject.toml.bak && \
	sed 's|[$$]{GITLAB_TOKEN}|'"$(GITLAB_TOKEN)"'|g' pyproject.toml.bak > pyproject.toml && \
	{ uv sync --no-cache --upgrade-package mirtolib; EXIT=$$?; mv pyproject.toml.bak pyproject.toml; exit $$EXIT; } || \
	{ mv pyproject.toml.bak pyproject.toml; exit 1; }

# Kind integration tests
KIND_CLUSTER := myrtus-test
KIND_CONTEXT := kind-$(KIND_CLUSTER)
KIND_IMAGE_REPO ?= myrtus-monitor
KIND_IMAGE_TAG ?= kind-test
KIND_LOCAL_IMAGE := $(KIND_IMAGE_REPO):$(KIND_IMAGE_TAG)
KIND_HELM_FLAGS := \
	--kube-context $(KIND_CONTEXT) \
	--namespace $(NAMESPACE) --create-namespace \
	--set image.repository=$(KIND_IMAGE_REPO) \
	--set image.tag=$(KIND_IMAGE_TAG) \
	--set image.pullPolicy=Never \
	--set image.pullSecret.enabled=false \
	--set global.liqoClusterId=kind-test-cluster \
	--set global.kbEndpoint=http://localhost:8080 \
	--set common.logLevel=DEBUG \
	--set nodeMonitor.kbDisabled=true \
	--set "tolerations[0].key=node-role.kubernetes.io/control-plane" \
	--set "tolerations[0].operator=Exists" \
	--set "tolerations[0].effect=NoSchedule"

kind-setup: ## Create kind cluster and load the local test image
	@command -v kind >/dev/null 2>&1 || { echo "$(RED)kind is required$(NC)"; exit 1; }
	@echo "$(ORANGE)Creating kind cluster '$(KIND_CLUSTER)'...$(NC)"
	@kind create cluster --name $(KIND_CLUSTER) 2>/dev/null || echo "$(YELLOW)Cluster already exists, reusing.$(NC)"
	@echo "$(ORANGE)Building and loading test image into kind...$(NC)"
	@docker build -f docker/Dockerfile --build-arg GITLAB_TOKEN=$(GITLAB_TOKEN) -t $(KIND_LOCAL_IMAGE) .
	@kind load docker-image $(KIND_LOCAL_IMAGE) --name $(KIND_CLUSTER)
	@echo "$(GREEN)Kind cluster ready.$(NC)"

kind-teardown: ## Delete the kind test cluster
	@echo "$(ORANGE)Deleting kind cluster '$(KIND_CLUSTER)'...$(NC)"
	@kind delete cluster --name $(KIND_CLUSTER)

kind-test-helm-value: ## Scenario 1 — node type resolved from Helm value (no node label)
	@echo "$(ORANGE)--- Scenario 1: node type from Helm value (nodeType=cloud) ---$(NC)"
	@helm upgrade --install $(PROJECT_NAME) $(HELM_CHART) $(KIND_HELM_FLAGS) \
		--set nodeMonitor.nodeType=cloud \
		--wait --timeout 90s
	@kubectl wait pod \
		-l app.kubernetes.io/name=$(PROJECT_NAME)-node-monitor \
		-n $(NAMESPACE) --context $(KIND_CONTEXT) \
		--for=condition=ready --timeout=60s
	@echo "$(YELLOW)Waiting for first collection cycle...$(NC)"
	@sleep 15
	@echo "$(ORANGE)--- Pod logs ---$(NC)"
	@kubectl logs \
		-l app.kubernetes.io/name=$(PROJECT_NAME)-node-monitor \
		-n $(NAMESPACE) --context $(KIND_CONTEXT) --tail=100
	@echo "$(ORANGE)--- Verification ---$(NC)"
	@kubectl logs \
		-l app.kubernetes.io/name=$(PROJECT_NAME)-node-monitor \
		-n $(NAMESPACE) --context $(KIND_CONTEXT) --tail=100 \
		| grep -q "'node_type': 'cloud'" \
		&& echo "$(GREEN)✓ PASS: node_type=cloud (from Helm value)$(NC)" \
		|| echo "$(RED)✗ FAIL: expected node_type=cloud in metrics$(NC)"
	@helm uninstall $(PROJECT_NAME) -n $(NAMESPACE) --kube-context $(KIND_CONTEXT) 2>/dev/null || true

kind-test-label-override: ## Scenario 2 — node type overridden by myrtus.io/node-type node label
	@echo "$(ORANGE)--- Scenario 2: node type from label override (label=fog, Helm=cloud) ---$(NC)"
	@echo "$(YELLOW)Labelling kind node with myrtus.io/node-type=fog...$(NC)"
	@kubectl label node $(KIND_CLUSTER)-control-plane myrtus.io/node-type=fog \
		--overwrite --context $(KIND_CONTEXT)
	@helm upgrade --install $(PROJECT_NAME) $(HELM_CHART) $(KIND_HELM_FLAGS) \
		--set nodeMonitor.nodeType=cloud \
		--wait --timeout 90s
	@kubectl wait pod \
		-l app.kubernetes.io/name=$(PROJECT_NAME)-node-monitor \
		-n $(NAMESPACE) --context $(KIND_CONTEXT) \
		--for=condition=ready --timeout=60s
	@echo "$(YELLOW)Waiting for first collection cycle...$(NC)"
	@sleep 15
	@echo "$(ORANGE)--- Pod logs ---$(NC)"
	@kubectl logs \
		-l app.kubernetes.io/name=$(PROJECT_NAME)-node-monitor \
		-n $(NAMESPACE) --context $(KIND_CONTEXT) --tail=100
	@echo "$(ORANGE)--- Verification ---$(NC)"
	@kubectl logs \
		-l app.kubernetes.io/name=$(PROJECT_NAME)-node-monitor \
		-n $(NAMESPACE) --context $(KIND_CONTEXT) --tail=100 \
		| grep -q "node_type resolved from node label.*fog" \
		&& echo "$(GREEN)✓ PASS: node_type inferred from label (fog)$(NC)" \
		|| echo "$(RED)✗ FAIL: expected label inference log for fog$(NC)"
	@kubectl logs \
		-l app.kubernetes.io/name=$(PROJECT_NAME)-node-monitor \
		-n $(NAMESPACE) --context $(KIND_CONTEXT) --tail=100 \
		| grep -q "'node_type': 'fog'" \
		&& echo "$(GREEN)✓ PASS: node_type=fog in metrics (overrode cloud from Helm)$(NC)" \
		|| echo "$(RED)✗ FAIL: expected node_type=fog in metrics$(NC)"
	@kubectl label node $(KIND_CLUSTER)-control-plane myrtus.io/node-type- \
		--context $(KIND_CONTEXT) 2>/dev/null || true
	@helm uninstall $(PROJECT_NAME) -n $(NAMESPACE) --kube-context $(KIND_CONTEXT) 2>/dev/null || true

kind-install: ## Install chart on kind cluster with test defaults (manual workflow)
	@helm upgrade --install $(PROJECT_NAME) $(HELM_CHART) $(KIND_HELM_FLAGS) \
		--set nodeMonitor.nodeType=cloud \
		--wait --timeout 90s
	@echo "$(GREEN)Chart installed. Follow logs with:$(NC)"
	@echo "  kubectl logs -f -l app.kubernetes.io/name=$(PROJECT_NAME)-node-monitor -n $(NAMESPACE) --context $(KIND_CONTEXT)"

kind-apply-label-override: ## Apply myrtus.io/node-type=fog label and restart pod to trigger re-inference
	@echo "$(ORANGE)Applying myrtus.io/node-type=fog label to node '$(KIND_CLUSTER)-control-plane'...$(NC)"
	@kubectl label node $(KIND_CLUSTER)-control-plane myrtus.io/node-type=fog \
		--overwrite --context $(KIND_CONTEXT)
	@echo "$(ORANGE)Restarting DaemonSet to trigger inference...$(NC)"
	@kubectl rollout restart daemonset $(PROJECT_NAME)-node-monitor \
		-n $(NAMESPACE) --context $(KIND_CONTEXT)
	@kubectl rollout status daemonset $(PROJECT_NAME)-node-monitor \
		-n $(NAMESPACE) --context $(KIND_CONTEXT) --timeout=60s
	@echo "$(ORANGE)--- Pod logs ---$(NC)"
	@kubectl logs -f -l app.kubernetes.io/name=$(PROJECT_NAME)-node-monitor \
		-n $(NAMESPACE) --context $(KIND_CONTEXT)

kind-test-all: kind-setup kind-test-helm-value kind-test-label-override kind-teardown ## Run both automated node type scenarios on kind (setup → test → teardown)
kind-demo: kind-setup kind-install kind-apply-label-override kind-teardown ## Manual workflow: setup → install → label override → teardown

all: clean install-dev build docker-build ## Run complete build pipeline
	@echo "$(GREEN)Complete build pipeline finished!$(NC)"

# Debug and Info
info: ## Show project information
	@echo "$(BLUE)Project Information:$(NC)"
	@echo "  Name: $(PROJECT_NAME)"
	@echo "  Python Version: $(PYTHON_VERSION)"
	@echo "  Docker Image: $(DOCKER_IMAGE)"
	@echo "  Helm Chart: $(HELM_CHART)"
	@echo "  Namespace: $(NAMESPACE)"
	@echo ""
	@echo "$(BLUE)Environment:$(NC)"
	@command -v uv >/dev/null 2>&1 && echo "  uv: $(GREEN)✓$(NC)" || echo "  uv: $(RED)✗$(NC)"
	@command -v docker >/dev/null 2>&1 && echo "  docker: $(GREEN)✓$(NC)" || echo "  docker: $(RED)✗$(NC)"
	@command -v helm >/dev/null 2>&1 && echo "  helm: $(GREEN)✓$(NC)" || echo "  helm: $(RED)✗$(NC)"
	@command -v kubectl >/dev/null 2>&1 && echo "  kubectl: $(GREEN)✓$(NC)" || echo "  kubectl: $(RED)✗$(NC)"