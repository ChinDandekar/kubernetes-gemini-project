# Define the namespace we want to ensure
DESIRED_NAMESPACE := react-frontend

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
	docker build -t frontend-image:latest .

tag:
	docker tag frontend-image:latest localhost:5000/frontend-image:latest

push:
	docker push localhost:5000/frontend-image:latest

delete:
	kubectl delete -n react-frontend deployment frontend

apply:
	kubectl apply -f deployment.yaml
	minikube tunnel

all:
	make build
	make tag
	make push
	make apply

start:
	make push
	make apply