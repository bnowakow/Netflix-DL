VENV ?= .venv
CODEX ?= codex

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

.PHONY: help build run cookies-copy cookies-remove codex-commit claude-commit github-sync install-skills codex-document
.DEFAULT_GOAL := help

help:
	@printf 'Netflix-DL targets\n\n'
	@printf '  \033[1;94m%s\033[0m\n' 'Application'
	@printf '    %-16s %s\n' 'build' 'Create the virtual environment and install dependencies'
	@printf '    %-16s %s\n' 'run' 'Open the download dialog or pass CLI options with ARGS'
	@printf '\n'
	@printf '  \033[1;94m%s\033[0m\n' 'Netflix cookies'
	@printf '    %-16s %s\n' 'cookies-copy' 'Copy the latest valid Netflix cookie export'
	@printf '    %-16s %s\n' 'cookies-remove' "Remove the app's imported and cached Netflix cookies"
	@printf '\n'
	@printf '  \033[1;94m%s\033[0m\n' 'Repository'
	@printf '    %-16s %s\n' 'github-sync' 'Sync upstream/main into the fork and merge main into bnowakow'
	@printf '    %-16s %s\n' 'codex-commit' 'Commit staged changes with Codex, and optionally push'
	@printf '    %-16s %s\n' 'claude-commit' 'Commit staged changes with Claude, and optionally push'
	@printf '    %-16s %s\n' 'install-skills' 'Install repository skills into the Codex user skills directory'
	@printf '    %-16s %s\n' 'codex-document' 'Refresh CHANGES_FROM_MAIN.md with Codex'

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

cookies-copy: $(VENV_PYTHON)
	"$(VENV_PYTHON)" copy_cookies.py

cookies-remove:
	$(RM) configs/Cookies/cookies.txt configs/Cookies/cookies_nf.txt

codex-commit:
	utilities/codex-commit.sh

claude-commit:
	utilities/claude-commit.sh

install-skills:
	@set -e; \
	destination="$${CODEX_HOME:-$$HOME/.codex}/skills"; \
	for skill in skills/*/SKILL.md; do \
		source_dir=$${skill%/SKILL.md}; \
		install_dir="$$destination/$${source_dir##*/}"; \
		mkdir -p "$$install_dir"; \
		cp -R "$$source_dir/." "$$install_dir/"; \
		printf 'Installed %s\n' "$$install_dir"; \
	done

codex-document:
	"$(CODEX)" exec --sandbox workspace-write 'Use the netflix-dl-document-changes skill at skills/netflix-dl-document-changes/SKILL.md. Follow its instructions and update CHANGES_FROM_MAIN.md.'

github-sync:
	@status=$$(git status --porcelain) && if [ -n "$$status" ]; then \
		echo "Commit or stash your changes before running make github-sync." >&2; \
		exit 1; \
	fi
	git fetch origin
	git fetch upstream
	git switch main
	git merge --ff-only origin/main
	git merge --ff-only upstream/main
	git switch bnowakow
	git merge --no-edit main
	git push --atomic origin main bnowakow
