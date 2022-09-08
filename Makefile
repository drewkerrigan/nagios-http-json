.PHONY: lint test coverage

lint:
	python -m pylint check_http_json.py
test:
	python -m unittest discover
coverage:
	python -m coverage run -m unittest discover
	python -m coverage report -m --include check_http_json.py
