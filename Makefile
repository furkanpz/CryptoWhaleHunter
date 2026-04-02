PYTHON ?= python3

.PHONY: run status test lint format check

run:
	$(PYTHON) -m crypto_whale_hunter run

status:
	$(PYTHON) -m crypto_whale_hunter status

test:
	$(PYTHON) -m unittest discover -s tests -v

lint:
	ruff check .

format:
	ruff format .

check:
	$(PYTHON) -m compileall crypto_whale_hunter tests
