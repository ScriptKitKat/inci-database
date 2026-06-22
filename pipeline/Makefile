.PHONY: install fmt lint test seed taxonomy wikidata enrich aliases pubmed editorial classify products help

VENV   ?= .venv
PYTHON ?= $(VENV)/bin/python3
PIP    ?= $(VENV)/bin/pip

help:
	@echo "Targets:"
	@echo "  install     create .venv and install pipeline deps"
	@echo "  fmt         ruff format"
	@echo "  lint        ruff check"
	@echo "  test        pytest"
	@echo "  seed        run full pipeline (stages 1..7 in order)"
	@echo "  taxonomy    stage 1:  seed ingredients from OBF taxonomy"
	@echo "  wikidata    stage 1b: enrich EC numbers and provenance via Wikidata"
	@echo "  enrich      stage 2:  pubchem enrichment"
	@echo "  aliases     stage 3:  open beauty facts alias harvest"
	@echo "  pubmed      stage 4:  pubmed abstract fetch (curated subset)"
	@echo "  pubmed-all  stage 4:  pubmed for all 22k ingredients (slow)"
	@echo "  editorial          stage 5: claude editorial via API (curated subset)"
	@echo "  editorial-all      stage 5: claude editorial for every ingredient -- expensive!"
	@echo "  editorial-export   stage 5: write prompt files for manual Claude.ai/ChatGPT paste"
	@echo "  editorial-import   stage 5: read pasted JSON responses back into the DB"
	@echo "  classify    stage 6:  tag classification"
	@echo "  products    stage 7:  seed products from OBF"
	@echo ""
	@echo "Override the interpreter with: make taxonomy PYTHON=/path/to/python"

install: $(VENV)/.installed

$(VENV)/.installed: pyproject.toml
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"
	@touch $@

fmt: install
	$(VENV)/bin/ruff format src tests

lint: install
	$(VENV)/bin/ruff check src tests

test: install
	$(VENV)/bin/pytest

seed: install
	$(PYTHON) -m inci_pipeline.cli run obf-taxonomy
	$(PYTHON) -m inci_pipeline.cli run wikidata
	$(PYTHON) -m inci_pipeline.cli run pubchem
	$(PYTHON) -m inci_pipeline.cli run obf-aliases
	$(PYTHON) -m inci_pipeline.cli run pubmed
	$(PYTHON) -m inci_pipeline.cli run editorial
	$(PYTHON) -m inci_pipeline.cli run classify

taxonomy:  install ; $(PYTHON) -m inci_pipeline.cli run obf-taxonomy
wikidata:  install ; $(PYTHON) -m inci_pipeline.cli run wikidata
enrich:    install ; $(PYTHON) -m inci_pipeline.cli run pubchem
aliases:   install ; $(PYTHON) -m inci_pipeline.cli run obf-aliases
pubmed:        install ; $(PYTHON) -m inci_pipeline.cli run pubmed
pubmed-all:    install ; $(PYTHON) -m inci_pipeline.cli run pubmed --all
editorial:        install ; $(PYTHON) -m inci_pipeline.cli run editorial
editorial-all:    install ; $(PYTHON) -m inci_pipeline.cli run editorial --all
editorial-export: install ; $(PYTHON) -m inci_pipeline.cli export-editorial-prompts
editorial-import: install ; $(PYTHON) -m inci_pipeline.cli import-editorial
classify:  install ; $(PYTHON) -m inci_pipeline.cli run classify
products:  install ; $(PYTHON) -m inci_pipeline.cli run products
