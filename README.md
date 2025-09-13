# rummikub-backend
Rummikub Backend

A Python FastAPI-based backend service for the Rummikub game.

## Running with Docker

### Using Docker directly

Build and run the Docker image:

```bash
# Build the image
docker build -t rummikub-backend .

# Run the container
docker run -p 8000:8000 rummikub-backend
```

### Using Docker Compose (Recommended)

For development and production deployment:

```bash
# Start the service
docker compose up

# Start in detached mode
docker compose up -d

# Stop the service
docker compose down
```

## API Endpoints

Once running, the API will be available at `http://localhost:8000`

- `GET /` - Root endpoint returning API information
- `GET /health` - Health check endpoint
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

## Development

The Docker Compose setup includes volume mounting for development. Changes to the code will be reflected in the running container.
