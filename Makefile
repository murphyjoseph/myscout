.PHONY: setup dev ingest score save target reset backup restore db test help

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  make %-12s %s\n", $$1, $$2}'

setup: ## Interactive onboarding wizard — profile + targets
	cd apps/worker && uv run python -m myscout setup

dev: ## Start Postgres + dashboard (full stack)
	./scripts/dev.sh

ingest: ## Fetch jobs from all configured connectors
	cd apps/worker && uv run python -m myscout ingest

score: ## Score jobs against your profile
	cd apps/worker && uv run python -m myscout score

save: ## Save a job URL — usage: make save URL=https://... OUTCOME=good_shot
	cd apps/worker && uv run python -m myscout save "$(URL)" --outcome $(or $(OUTCOME),good_shot)

target: ## Add a target company — usage: make target COMPANY=Stripe [TYPE=auto] [SLUG=stripe] [URL=...]
	cd apps/worker && uv run python -m myscout add-target $(if $(COMPANY),"$(COMPANY)",) $(if $(TYPE),--type $(TYPE),) $(if $(SLUG),--slug $(SLUG),) $(if $(URL),--url "$(URL)",)

backup: ## Snapshot the database to backups/
	./scripts/backup.sh

restore: ## Restore from backup — usage: make restore FILE=backups/<name>.dump
	./scripts/restore.sh $(FILE)

reset: ## Destroy and recreate the database (offers backup first)
	./scripts/reset.sh

test: ## Run Python backend tests
	cd apps/worker && uv run pytest -v

db: ## Open psql shell
	docker exec -it myscout-postgres psql -U myscout -d myscout
