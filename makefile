SHELL := /bin/bash
.ONESHELL:

.venv: pyproject.toml
	echo "running .venv..."
	poetry install
	touch .venv

node_modules: package.json
	yarn install
	touch node_modules

migrations := $(wildcard */migrations/*.py)

.git/first_run: .venv
	echo "running .git/first_run..."
	# pre-commit install -t pre-commit -t pre-push -t commit-msg --overwrite
	# touch .git/first_run

clean:
	rm -vf .git/first_run
	rm -vf .git/hooks/{pre-{commit,push},commit-msg}
	rm -rf .venv
	rm -rf node_modules
	find . -type d -name "dist" ! -path "*node_modules*" -exec rm -rfv '{}' \;

web: .venv $(migrations) .git/first_run
	poetry install
	poetry run python manage.py runserver 0.0.0.0:8000

node: node_modules
	yarn run watch

ci:
	poetry run pre-commit run --show-diff-on-failure --color=always --all-files --hook-stage push

test:
	yarn run test --watchAll=false
	poetry run pytest -n 8 -ra -q --disable-warnings --tb=long

dev_image:
	mkdir -p keypairs
	cp -r ~/.ssh/* keypairs/

	docker build -f Dockerfile.dev \
		-t eznashdb-dev-image:latest .

	rm -rf keypairs

.PHONY: clean node web ci test dev_image
