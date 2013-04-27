VENV = .venv
ENABLE = $(VENV)/bin/activate
PROJ = mongomodel

clean:
	find ./ -name "*~" -exec rm {} \;
	find ./ -name "*.pyc" -exec rm {} \;
	find ./ -name "*.pyo" -exec rm {} \;
	find . -name "*.sw[op]" -exec rm {} \;
	rm -rf _trial_temp/ build/ dist/ MANIFEST \
		CHECK_THIS_BEFORE_UPLOAD.txt *.egg-info

build-venv:
	virtualenv $(VENV)
	. $(ENABLE) && pip install twisted
	. $(ENABLE) && pip install txmongo

check: build-venv
	clear
	@. $(ENABLE) && trial $(PROJ)

clean-venv:
	rm -rf $(VENV)

register:
	python setup.py register

upload: check
	python setup.py sdist upload --show-response
