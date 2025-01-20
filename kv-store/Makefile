build:
	docker build -t kvstore-image:latest .

tag:
	docker tag kvstore-image:latest localhost:5000/kvstore-image:latest

push:
	docker push localhost:5000/kvstore-image:latest

delete:
	kubectl delete -n kvstore statefulset kvstore

create-registry:
	docker run -d -p 64005:5000 --name localregistry registry:2

all:
	make build
	make tag
	make push
	kubectl apply -f kvstore-stateful.yaml