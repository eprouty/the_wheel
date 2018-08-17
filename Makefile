init:
	python3 -m venv .venv

test:
	python3 -m unittest

coverage:
	coverage run --source the_wheel -m unittest

server:
	python3 server.py

deploy:
	git push heroku master

.PHONY: init test coverage server deploy
