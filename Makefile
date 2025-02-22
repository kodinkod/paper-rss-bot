.PHONY: all lint format fix

all: lint format

ruff-lint:
	ruff check .

fruff-ormat:
	ruff format .

ruff-fix:
	ruff check --fix .