build:
	docker build -t kvstore-image:latest .

tag:
	docker tag kvstore-image:latest localhost:5000/kvstore-image:latest

push:
	docker push localhost:5000/kvstore-image:latest

delete:
	kubectl delete -n kvstore statefulset kvstore

apply:
	kubectl apply -f kvstore-stateful.yaml


setup:
	make push
	kubectl config set-context --current --namespace=kvstore
	kubectl apply -f role.yaml
	kubectl apply -f rolebinding.yaml
	kubectl apply -f kvstore-internal.yaml
	kubectl apply -f kvstore-external.yaml
	make apply

all:
	make build
	make tag
	make push