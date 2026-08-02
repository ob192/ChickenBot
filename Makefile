DOCKERHUB_USER = sasha192bunin
IMAGE = $(DOCKERHUB_USER)/chickenbot
ADMIN_IMAGE = $(IMAGE)-admin
TAG = latest
ENV_FILE = .env
API_PORT = 8000

.PHONY: run bot api admin dev build build-admin deploy up stop logs

## Run the Telegram bot locally with uv
bot:
	uv run python -m telegram_bot.main

## Backwards-compatible alias for `make bot`
run: bot

## Run the FastAPI service locally (auto-reload) — http://localhost:$(API_PORT)/docs
api:
	uv run uvicorn api.main:app --reload --port $(API_PORT)

## Run the Next.js admin UI locally — http://localhost:3000
admin:
	cd admin && npm run dev

## Everything at once with docker compose (bot + api + admin)
dev:
	docker compose up --build

## Build the python docker image (bot + api)
build:
	docker build -t $(IMAGE):$(TAG) .

## Build the admin UI docker image
build-admin:
	docker build -t $(ADMIN_IMAGE):$(TAG) ./admin

## Build and publish both images to Docker Hub
deploy: build build-admin
	docker push $(IMAGE):$(TAG)
	docker push $(ADMIN_IMAGE):$(TAG)

## Start the whole stack in the background
up:
	docker compose --env-file $(ENV_FILE) up -d
	docker compose logs -f --tail 20

## Stop and remove the stack
stop:
	docker compose down

## Follow logs of all services
logs:
	docker compose logs -f
