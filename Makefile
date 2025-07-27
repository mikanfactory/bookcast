.PHONY: lint
lint:
	uv run ruff check src experiment tests

.PHONY: format
format:
	uv run ruff format src experiment tests && uv run ruff check --fix src experiment tests

.PHONY: test
test:
	uv run pytest tests
