# Define the namespace we want to ensure
DESIRED_NAMESPACE := kvstore

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
	docker build -t kvstore-image:latest .

tag:
	docker tag kvstore-image:latest localhost:5000/kvstore-image:latest

push:
	docker push localhost:5000/kvstore-image:latest

delete:
	kubectl delete -n kvstore statefulset kvstore

apply:
	kubectl config set-context --current --namespace=kvstore
	kubectl apply -f kvstore-stateful.yaml


setup:
	kubectl apply -f role.yaml
	kubectl apply -f rolebinding.yaml
	kubectl apply -f kvstore-internal.yaml
	kubectl apply -f kvstore-external.yaml
	make apply

all:
	make build
	make tag
	make push