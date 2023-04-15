.PHONY: install run

install:
	pip install -r requirements.txt

run:
	export FLASK_APP=server.py && \
	export FLASK_DEBUG=1 && \
	flask run

