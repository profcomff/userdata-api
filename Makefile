run:
	source ./venv/bin/activate && uvicorn --reload --log-config logging_dev.conf userdata_api.routes.base:app

configure: venv
	source ./venv/bin/activate && pip install -r requirements.dev.txt -r requirements.txt

venv:
	python3.11 -m venv venv

format:
	autoflake -r --in-place --remove-all-unused-imports ./userdata_api
	isort ./userdata_api
	black ./userdata_api
	source ./venv/bin/activate && autoflake -r --in-place --remove-all-unused-imports ./tests
	source ./venv/bin/activate && isort ./tests
	source ./venv/bin/activate && black ./tests
	source ./venv/bin/activate && autoflake -r --in-place --remove-all-unused-imports ./migrations
	source ./venv/bin/activate && isort ./migrations
	source ./venv/bin/activate && black ./migrations

db:
	docker run -d -p 5432:5432 -e POSTGRES_HOST_AUTH_METHOD=trust --name db-userdata_api postgres:15

migrate:
	alembic upgrade head
