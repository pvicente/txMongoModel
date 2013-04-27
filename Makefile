VENV = .venv
ENABLE = $(VENV)/bin/activate
PROJ = mongomodel

build-venv:
	virtualenv $(VENV)
	. $(ENABLE) && pip install twisted
	. $(ENABLE) && pip install txmongo

check: build-venv
	clear
	@. $(ENABLE) && trial $(PROJ)

register:
	python setup.py register

upload: check
	python setup.py sdist upload --show-response
