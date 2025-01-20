
# Define the namespace we want to ensure
DESIRED_NAMESPACE := backend-api

# This is a special target that will be run before every other target
.PHONY: check-namespace
check-namespace:
	@if [ "$$(kubectl config view --minify --output 'jsonpath={..namespace}')" != "$(DESIRED_NAMESPACE)" ]; then \
		echo "Switching to $(DESIRED_NAMESPACE) namespace"; \
		kubectl config set-context --current --namespace=$(DESIRED_NAMESPACE); \
	fi

# Make all targets depend on check-namespace
%: check-namespace
	@true

build:
	docker build -t backend-image:latest .

tag:
	docker tag backend-image:latest localhost:5000/backend-image:latest

push:
	docker push localhost:5000/backend-image:latest

delete:
	kubectl delete -n backend-api deployment fastapi-backend

apply:
	kubectl apply -f deployment.yaml

all:
	make build
	make tag
	make push
	make apply
	