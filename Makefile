.PHONY: lint
lint:
	uv run ruff check src tests

.PHONY: format
format:
	uv run ruff format src tests && uv run ruff check --fix src tests

.PHONY: test
test:
	uv run pytest tests

.PHONY: test/integration
test/integration:
	uv run pytest -m integration tests

.PHONY: db/clean
db/clean:
	supabase db reset --local --yes

deploy:
	docker tag bookcast us-central1-docker.pkg.dev/hedgehog-fm/bookcast/bookcast-server && \
	docker push us-central1-docker.pkg.dev/hedgehog-fm/bookcast/bookcast-server
