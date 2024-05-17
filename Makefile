.PHONY: lint test coverage

PYTHON_PATH?=python3

lint:
	$(PYTHON_PATH) -m pylint check_http_json.py
test:
	$(PYTHON_PATH) -m unittest discover
coverage:
	$(PYTHON_PATH) -m coverage run -m unittest discover
	$(PYTHON_PATH) -m coverage report -m --include check_http_json.py
