.PHONY: install help bulk-import

PYTHON = bin/python

help:
	@echo "Available commands:"
	@echo "  make install      - Set up project (create .env from .env.dist if needed)"
	@echo "  make bulk-import  - Run bulk import of all Zendesk articles"

install:
	@if [ ! -f .env ]; then \
		echo "Creating .env file from .env.dist..."; \
		cp .env.dist .env; \
		echo "✓ .env file created. Please update with your actual values."; \
	else \
		echo "✓ .env file already exists, skipping..."; \
	fi
	@docker compose build python

bulk-import:
	@$(PYTHON) -m src.cli.bulk_import
