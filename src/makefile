NAME = "src"

all: run

install:
	@echo "Installing dependencies..."
	@uv sync

install-active:
	@echo "Installing dependencies for active venv..."
	@uv sync --active

run:
	@echo "Running the application..."
	@uv run -m $(NAME)

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete