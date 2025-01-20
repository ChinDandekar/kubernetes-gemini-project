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
	