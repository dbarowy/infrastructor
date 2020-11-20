SHELL:=/bin/bash
INSTALLDIR=/usr/local/bin/cs

.PHONY: install setup

setup:
	python3 -m venv venv
