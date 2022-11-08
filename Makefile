.DEFAULT_GOAL := help

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort -k 1,1 | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: start
start: ## Start the development server
	@docker-compose up -d --build

.PHONY: stop
stop: ## Stop the development server
	@docker-compose stop

.PHONY: lint
lint: ## Lint the project
	@docker-compose exec backend sh -c "poetry run black --check . && poetry run flake8"

.PHONY: format-code
format-code: ## Format the backend code
	@docker-compose exec backend sh -c "poetry run black . && poetry run isort ."

.PHONY: test
test: ## Test the project
	@docker-compose exec backend sh -c "poetry run black . && poetry run isort . && poetry run pytest --no-cov-on-fail --cov"

.PHONY: bash
bash: ## Shell into the backend
	@docker-compose exec backend bash

.PHONY: dbshell
dbshell: ## Start a psql shell
	@docker-compose exec db psql -Utimed timed

.PHONY: shell_plus
shell_plus: ## Run shell_plus
	@docker-compose exec backend poetry run python manage.py shell_plus

.PHONY: makemigrations
makemigrations: ## Make django migrations
	@docker-compose exec backend poetry run python manage.py makemigrations

.PHONY: migrate
migrate: ## Migrate django
	@docker-compose exec backend poetry run python manage.py migrate

.PHONY: debug-backend
debug-backend: ## Start backend container with service ports for debugging
	@docker-compose run --service-ports backend

.PHONY: flush
flush: ## Flush database contents
	@docker-compose exec backend poetry run python manage.py flush --no-input

.PHONY: loaddata
loaddata: flush ## Loads test data into the database
	@docker-compose exec backend poetry run python manage.py loaddata timed/fixtures/test_data.json
