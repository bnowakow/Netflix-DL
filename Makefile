VENV ?= .venv

ifeq ($(OS),Windows_NT)
PYTHON ?= python
VENV_PYTHON := $(VENV)/Scripts/python.exe
else
PYTHON ?= $(shell for candidate in python3.10 python3.9 python3.8 python3 /usr/bin/python3; do \
	"$$candidate" -c 'import sys; sys.exit(not ((3, 8) <= sys.version_info[:2] <= (3, 10)))' 2>/dev/null \
		&& { echo "$$candidate"; break; }; \
done)
VENV_PYTHON := $(VENV)/bin/python
endif

.PHONY: build run copy-cookies claude-commit
build: $(VENV)/.requirements-installed

$(VENV_PYTHON):
	$(if $(strip $(PYTHON)),,$(error Python 3.8–3.10 is required. Install it or set PYTHON to its executable))
	"$(PYTHON)" -m venv "$(VENV)"

$(VENV)/.requirements-installed: requirements.txt $(VENV_PYTHON)
	"$(VENV_PYTHON)" -m pip install -r requirements.txt
	"$(VENV_PYTHON)" -c "from pathlib import Path; Path(r'$@').touch()"

run: build
ifeq ($(origin ARGS),undefined)
	"$(VENV_PYTHON)" run_dialog.py
else
	"$(VENV_PYTHON)" NFripper.py $(ARGS)
endif

copy-cookies: $(VENV_PYTHON)
	"$(VENV_PYTHON)" copy_cookies.py

claude-commit:
	utilities/claude-commit.sh
