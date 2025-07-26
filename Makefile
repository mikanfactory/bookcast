.PHONY: lint
lint:
	uv run ruff check src experiment tests --fix

.PHONY: format
format:
	uv run ruff format src experiment tests

.PHONY: test
test:
	uv run pytest tests
