.PHONY: install lint format typecheck security complexity test coverage all clean

install:
	pip install -r requirements.txt
	pre-commit install

lint:
	ruff check src/ tests/
	black --check src/ tests/
	isort --check-only src/ tests/

format:
	ruff check --fix src/ tests/
	ruff format src/ tests/
	black src/ tests/
	isort src/ tests/

typecheck:
	mypy src/n2s_estimator/

security:
	bandit -r src/n2s_estimator

complexity:
	radon cc -s -a src/n2s_estimator

test:
	pytest -q

coverage:
	pytest --cov=src/n2s_estimator --cov-report=term-missing

all: format lint typecheck security test coverage

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov/ .mypy_cache

