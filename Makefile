VENV = .venv
ENABLE = $(VENV)/bin/activate
PROJ = mongomodel

build-venv:
	virtualenv $(VENV)
	. $(ENABLE) && pip install twisted
	. $(ENABLE) && pip install txmongo

check: build-venv
	. $(ENABLE) && trial $(PROJ)
