.PHONY: help install test train run bot clean

help:
	@echo "Available commands:"
	@echo "  make install   Install dependencies"
	@echo "  make test      Run tests"
	@echo "  make train     Train the model"
	@echo "  make run       Run web app"
	@echo "  make bot       Run Telegram bot"
	@echo "  make clean     Clean project"

install:
	pip install -r requirements.txt
	pre-commit install

test:
	pytest tests/ -v

train:
	python src/model_trainer.py

run:
	streamlit run src/app.py

bot:
	python src/telegram_bot.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

format:
	black src/
	isort src/

lint:
	flake8 src/
	mypy src/

pre-commit:
	pre-commit run --all-files
