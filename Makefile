shutdown:
	$(MAKE) -C react-frontend delete
	$(MAKE) -C kv-store delete
	$(MAKE) -C backend-api delete

startup:
	$(MAKE) -C kv-store apply
	$(MAKE) -C backend-api apply
	$(MAKE) -C react-frontend apply
