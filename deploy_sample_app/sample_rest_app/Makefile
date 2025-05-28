# Makefile (opcjonalne - dla ułatwienia)
.PHONY: build run test clean

# Build Docker image
build:
	docker build -t sample_rest_app:latest .

# Run with docker-compose (for local testing)
run:
	docker-compose up --build

# Run only the app (assumes external PostgreSQL)
run-app:
	docker run -p 8080:8080 \
		-e DB_HOST=your-rds-endpoint \
		-e DB_NAME=appdb \
		-e DB_USER=dbuser \
		-e DB_PASSWORD=your-password \
		flask-app:latest

# Test endpoints
test:
	@echo "Testing health endpoint..."
	curl -X GET http://localhost:8080/
	@echo "\nTesting database connection..."
	curl -X GET http://localhost:8080/db-test
	@echo "\nCreating test user..."
	curl -X POST http://localhost:8080/users \
		-H "Content-Type: application/json" \
		-d '{"name":"John Doe","email":"john@example.com"}'
	@echo "\nGetting users..."
	curl -X GET http://localhost:8080/users

# Clean up
clean:
	docker-compose down -v
	docker rmi flask-app:latest || true