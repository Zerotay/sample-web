#!/bin/zsh
DOCKERNAME=zerotay
TAG=0.1.0
docker buildx build --platform linux/amd64,linux/arm64 \
	--push --build-arg TAG=$TAG \
	--tag $DOCKERNAME/zero-web:$TAG --tag $DOCKERNAME/zero-web:latest \
	.
