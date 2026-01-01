IMAGE ?= filefrog/llm-studio
TAG ?= latest

fmt:
	isort *.py bin/*
	black *.py bin/*

build: fmt
	docker build -t $(IMAGE):$(TAG) .
push: build
	docker push $(IMAGE):$(TAG)
