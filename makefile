.PHONY: lint test coverage

lint:
	python3 -m pylint check_http_json.py
test:
	python3 -m unittest discover
coverage:
	python3 -m coverage run -m unittest discover
	python3 -m coverage report -m --include check_http_json.py
