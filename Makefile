DOCKERHUB_USER = sasha192bunin
IMAGE = $(DOCKERHUB_USER)/chickenbot
TAG = latest
CONTAINER = chickenbot
ENV_FILE = .env

.PHONY: run build deploy up stop logs

## Run the bot locally with uv
run:
	uv run python main.py

## Build the docker image
build:
	docker build -t $(IMAGE):$(TAG) .

## Build and publish the image to Docker Hub
deploy: build
	docker push $(IMAGE):$(TAG)

## Run the published image as a local container
up:
	docker rm -f $(CONTAINER) 2>/dev/null || true
	docker run -d \
		--name $(CONTAINER) \
		--restart unless-stopped \
		--env-file $(ENV_FILE) \
		$(IMAGE):$(TAG)
	docker logs -f --tail 20 $(CONTAINER)

## Stop and remove the container
stop:
	docker rm -f $(CONTAINER)

## Follow container logs
logs:
	docker logs -f $(CONTAINER)
