help:
	@echo "Please use 'make <target>' where <target> is one of"
	@echo "  format      to format the code"


# Variables
PYTHON_FILES := $(shell find . -name "*.py")
PYTHON_VERSION := 3.9
format:
	@echo "Formatting Python code..."
	pip3 install black
	pip3 install isort
	black src
	isort src
	@black $(PYTHON_FILES)
	@isort $(PYTHON_FILES)
	@echo "Done!"
clean:
	find . -name "__pycache__" -exec rm -r {} +
	find . -name "*.pyc" -exec rm -f {} +


