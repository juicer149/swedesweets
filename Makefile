# Load local settings from .env when present (see .env.example).
-include .env
export

PYTHON := .venv/bin/python
PIP := .venv/bin/pip
MANAGE := $(PYTHON) manage.py

.PHONY: help venv install setup run check lint migrate makemigrations superuser seed reset-demo shell django-shell collectstatic messages compilemessages i18n test test-v clean css-unused

help:
	@echo "SwedeSweets Ops commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install         Install project dependencies from pyproject.toml"
	@echo "  make setup           Create venv, install deps, migrate database"
	@echo ""
	@echo "Django:"
	@echo "  make run             Run development server"
	@echo "  make check           Run Django system checks"
	@echo "  make migrate         Apply migrations"
	@echo "  make makemigrations  Create new migrations"
	@echo "  make superuser       Create Django superuser"
	@echo "  make seed            Seed demo data"
	@echo "  make reset-demo      Reset and seed demo data"
	@echo "  make collectstatic   Build static files manifest"
	@echo ""
	@echo "Translations:"
	@echo "  make messages        Update French translation messages"
	@echo "  make compilemessages Compile translation messages"
	@echo "  make i18n            Update and compile translations"
	@echo ""
	@echo "Tools:"
	@echo "  make shell           Run shell_plus with IPython"
	@echo "  make django-shell    Run default Django shell"
	@echo "  make lint            Run ruff"
	@echo "  make css-unused      List CSS classes nothing uses any more"
	@echo "  make test            Run tests"
	@echo "  make test-v          Run verbose tests"
	@echo "  make clean           Remove Python/tool caches"

venv: $(PYTHON)

$(PYTHON):
	python3 -m venv .venv

install: venv
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

setup: install migrate collectstatic

run:
	$(MANAGE) runserver 0.0.0.0:8000

check:
	$(MANAGE) check

migrate:
	$(MANAGE) migrate

makemigrations:
	$(MANAGE) makemigrations

superuser:
	$(MANAGE) createsuperuser

seed:
	$(MANAGE) seed_demo_data --with-orders --with-demo-accounts --with-images

reset-demo:
	$(MANAGE) seed_demo_data --reset --with-orders --with-demo-accounts --with-images

collectstatic:
	$(MANAGE) collectstatic --noinput -v 0

messages:
	$(MANAGE) makemessages -l fr

compilemessages:
	$(MANAGE) compilemessages

i18n: messages compilemessages

shell:
	$(MANAGE) shell_plus --ipython

django-shell:
	$(MANAGE) shell

lint:
	.venv/bin/ruff check .

css-unused:
	$(PYTHON) tools/css_unused.py

test: collectstatic
	$(PYTHON) -m pytest

test-v: collectstatic
	$(PYTHON) -m pytest -v

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
