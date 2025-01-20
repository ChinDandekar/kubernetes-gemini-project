shutdown:
	$(MAKE) -C react-frontend delete
	$(MAKE) -C kv-store delete
	$(MAKE) -C backend-api delete

apply:
	$(MAKE) -C kv-store apply
	$(MAKE) -C backend-api apply
	$(MAKE) -C react-frontend apply

startup:
	$(MAKE) -C kv-store setup
	$(MAKE) -C backend-api setup
	$(MAKE) -C react-frontend setup