.PHONY: all install format lint test generate-client

# Default OpenAPI spec URL - can be overridden via command line
OPENAPI_URL ?= http://localhost:8088/openapi.json

all: install format lint test generate-client

install:
	poetry install

format:
	poetry run isort .
	poetry run black .

lint:
	poetry run mypy .

test:
	poetry run pytest -k "not e2e"

generate-client:
	poetry run openapi-python-client generate \
		--url $(OPENAPI_URL) \
		--meta none \
		--output-path cp_agent/generated \
		--overwrite