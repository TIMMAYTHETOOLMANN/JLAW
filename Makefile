.PHONY: help build run test verify investigate analyze monitor clean logs shell

# Variables
IMAGE_NAME = jlaw-forensics
IMAGE_TAG = latest
CONTAINER_NAME = jlaw-forensics-container

help: ## Show this help message
	@echo "JLAW Forensic System - Docker Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Build Docker image
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) .
	@echo "✅ Image built: $(IMAGE_NAME):$(IMAGE_TAG)"

build-no-cache: ## Build Docker image without cache
	docker build --no-cache -t $(IMAGE_NAME):$(IMAGE_TAG) .
	@echo "✅ Image built (no cache): $(IMAGE_NAME):$(IMAGE_TAG)"

run: ## Run container interactively
	docker run -it --rm \
		-v $(PWD)/data:/var/forensic/worm \
		-v $(PWD)/logs:/app/logs \
		--name $(CONTAINER_NAME) \
		$(IMAGE_NAME):$(IMAGE_TAG) /bin/bash

verify: ## Run system integrity verification
	docker run --rm $(IMAGE_NAME):$(IMAGE_TAG) verify

test: ## Run basic tests
	docker run --rm $(IMAGE_NAME):$(IMAGE_TAG) verify
	@echo "✅ Tests passed"

investigate: ## Run investigation (set CIK and NAME variables)
	docker run --rm \
		-e GOVINFO_API_KEY="${GOVINFO_API_KEY}" \
		-v $(PWD)/results:/app/results \
		$(IMAGE_NAME):$(IMAGE_TAG) investigate \
		--cik $(CIK) \
		--name "$(NAME)" \
		--years 3 \
		--output /app/results/$(CIK)_investigation.json

analyze: ## Analyze single filing (set CIK and ACCESSION variables)
	docker run --rm \
		-e GOVINFO_API_KEY="${GOVINFO_API_KEY}" \
		$(IMAGE_NAME):$(IMAGE_TAG) analyze \
		--cik $(CIK) \
		--accession $(ACCESSION)

compose-up: ## Start services with docker-compose
	docker-compose up -d
	@echo "✅ Services started"

compose-down: ## Stop services with docker-compose
	docker-compose down
	@echo "✅ Services stopped"

compose-logs: ## View docker-compose logs
	docker-compose logs -f

monitor: ## Run continuous monitoring
	docker-compose up -d jlaw-monitor
	@echo "✅ Monitoring started - press Ctrl+C to stop logs"
	docker-compose logs -f jlaw-monitor

logs: ## View container logs
	docker logs -f $(CONTAINER_NAME)

shell: ## Open shell in running container
	docker exec -it $(CONTAINER_NAME) /bin/bash

clean: ## Remove containers, images, and volumes
	docker-compose down -v 2>/dev/null || true
	docker rm -f $(CONTAINER_NAME) 2>/dev/null || true
	docker rmi $(IMAGE_NAME):$(IMAGE_TAG) 2>/dev/null || true
	@echo "✅ Cleaned up"

clean-all: ## Remove all forensic-related Docker resources
	docker-compose down -v
	docker rm -f $$(docker ps -a -q --filter name=jlaw) 2>/dev/null || true
	docker rmi $$(docker images -q $(IMAGE_NAME)) 2>/dev/null || true
	docker volume rm $$(docker volume ls -q --filter name=forensic) 2>/dev/null || true
	@echo "✅ All resources cleaned"

ps: ## List running containers
	docker ps --filter name=jlaw

images: ## List forensic images
	docker images | grep jlaw

volumes: ## List forensic volumes
	docker volume ls | grep forensic

stats: ## Show container resource usage
	docker stats --no-stream $$(docker ps --filter name=jlaw -q)

backup: ## Backup forensic data volume
	mkdir -p backups
	docker run --rm \
		-v forensic-data:/data \
		-v $(PWD)/backups:/backup \
		alpine tar czf /backup/forensic-data-$$(date +%Y%m%d-%H%M%S).tar.gz -C /data .
	@echo "✅ Backup created in backups/"

restore: ## Restore forensic data volume (set BACKUP_FILE variable)
	docker run --rm \
		-v forensic-data:/data \
		-v $(PWD)/backups:/backup \
		alpine tar xzf /backup/$(BACKUP_FILE) -C /data
	@echo "✅ Data restored from $(BACKUP_FILE)"

push: ## Push image to registry (set REGISTRY variable)
	docker tag $(IMAGE_NAME):$(IMAGE_TAG) $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
	docker push $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
	@echo "✅ Image pushed to $(REGISTRY)"

pull: ## Pull image from registry (set REGISTRY variable)
	docker pull $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
	docker tag $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG) $(IMAGE_NAME):$(IMAGE_TAG)
	@echo "✅ Image pulled from $(REGISTRY)"

# Example usage targets
example-tesla: ## Example: Investigate Tesla
	$(MAKE) investigate CIK=0001318605 NAME="Tesla Inc"

example-apple: ## Example: Investigate Apple
	$(MAKE) investigate CIK=0000320193 NAME="Apple Inc"

example-alphabet: ## Example: Investigate Alphabet
	$(MAKE) investigate CIK=0001652044 NAME="Alphabet Inc"

