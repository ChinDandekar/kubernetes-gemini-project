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