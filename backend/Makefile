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

.PHONY: db/start
db/start:
	supabase start \
	  --exclude gotrue,realtime,storage-api,imgproxy,kong, \
				inbucket,pgadmin-schema-diff,migra,postgres-meta, \
				studio,edge-runtime,logflare,vector

.PHONY: db/clean
db/clean:
	supabase db reset --local --yes


include .env
IMAGE := $(GOOGLE_CLOUD_LOCATION)-docker.pkg.dev/$(GOOGLE_CLOUD_PROJECT)/bookcast/bookcast-server
.PHONY: deploy/server
deploy/server:
	docker build --platform=linux/amd64 -t bookcast-server . && \
	docker tag bookcast-server $(IMAGE) && \
	docker push $(IMAGE) && \
	gcloud run deploy bookcast-server \
		--image=$(IMAGE):latest \
		--set-env-vars=ENV=production \
		--region=$(GOOGLE_CLOUD_LOCATION) \
		--project=$(GOOGLE_CLOUD_PROJECT) && \
	gcloud run services --region $(GOOGLE_CLOUD_LOCATION) update-traffic bookcast-server --to-latest
