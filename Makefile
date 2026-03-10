PYTHON ?= python3
VENV ?= venv

.PHONY: install test run

install:
	$(PYTHON) -m venv $(VENV)
	. $(VENV)/bin/activate && pip install -r requirements.txt

test:
	. $(VENV)/bin/activate && pytest

run:
	. $(VENV)/bin/activate && streamlit run app.py
