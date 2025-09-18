# Rummikub Backend API

A Python-based REST API for playing Rummikub online. This backend provides game logic, session management, and all necessary endpoints to play Rummikub without requiring user registration.

## Features

- 🎮 Complete Rummikub game logic implementation
- 🔐 JWT-based authentication (no user registration required)
- 🌐 Web interface for playing games in browser
- 🎫 Simple game joining system with game IDs
- 🗄️ Redis data storage with volume persistence
- 🐳 Docker support for easy deployment
- 📋 RESTful API with comprehensive game state management
- 📊 Real-time game state updates

## Game Rules

See [RUMMIKUB_RULES.md](RUMMIKUB_RULES.md) for complete game rules and gameplay instructions.

## Data Storage

The application uses **Redis** for persistent data storage with Docker volume support:

- **Persistence**: Game data survives container restarts
- **Performance**: Optimized Redis data structures and caching
- **Volume Configuration**: Data stored in `redis_data` Docker volume
- **Fallback Mode**: Automatic fallback to in-memory storage if Redis is unavailable

For detailed Redis setup and volume configuration, see [REDIS_VOLUME_CONFIG.md](REDIS_VOLUME_CONFIG.md).

### Environment Variables
- `REDIS_HOST`: Redis server hostname (default: `redis`)
- `REDIS_PORT`: Redis server port (default: `6379`)
- `REDIS_DB`: Redis database number (default: `0`)

## API Documentation

### OpenAPI Specification
A complete OpenAPI 3.1.0 specification is available in the repository:
- **Static file**: [`openapi.json`](openapi.json) - Version-controlled OpenAPI specification
- **Live documentation**: Available when server is running:
  - Swagger UI: `http://localhost:8090/docs`
  - ReDoc: `http://localhost:8090/redoc`
  - OpenAPI JSON: `http://localhost:8090/openapi.json`

To regenerate the OpenAPI specification file:
```bash
python generate_openapi.py
```

## API Endpoints

### Authentication

#### Game Creation (Admin Only)
- **Basic Authentication** required for creating new games:
  - Username: `admin` 
  - Password: `admin` (configurable via `ADMIN_PASSWORD` environment variable)

#### Game Operations (Players)
- **JWT Bearer Token** required for all game operations after joining
- Tokens are obtained when joining a game
- Include token in Authorization header: `Authorization: Bearer <token>`
- Tokens expire after 24 hours

### Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | Web interface & API information | No |
| POST | `/game` | Create new game | Yes (Basic Auth) |
| POST | `/game/{game_id}/join` | Join game with player name | No |
| GET | `/game/{game_id}` | Get game state | Yes (Bearer Token) |
| POST | `/game/{game_id}/action` | Perform game action | Yes (Bearer Token) |
| GET | `/game/{game_id}/info` | Get basic game info | No |

## Quick Start

### Using Docker (Recommended)

1. **Clone and build:**
   ```bash
   git clone <repository-url>
   cd rummikub-backend
   docker-compose up --build
   ```

2. **API will be available at:** `http://localhost:8090`

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the server:**
   ```bash
   python main.py
   ```

3. **API will be available at:** `http://localhost:8090`

### Makefile Targets

The project includes a Makefile for development tasks:

```bash
make help          # Show available targets
make test          # Run all tests and validation
make clean         # Clean build artifacts
```

## Usage Example

### 1. Create a Game
```bash
curl -X POST "http://localhost:8090/game" \
  -H "Content-Type: application/json" \
  -u "admin:admin" \
  -d '{"max_players": 4, "name": "GameHost"}'
```

Response:
```json
{
  "game_id": "game-uuid",
  "max_players": 4,
  "creator_name": "GameHost",
  "status": "waiting",
  "message": "Game created successfully"
}
```

### 2. Join a Game
```bash
curl -X POST "http://localhost:8090/game/{game_id}/join" \
  -H "Content-Type: application/json" \
  -d '{"player_name": "PlayerName"}'
```

Response:
```json
{
  "access_token": "jwt-token-here",
  "token_type": "bearer",
  "game_id": "game-uuid",
  "player_name": "PlayerName",
  "message": "Successfully joined game",
  "game_state": {...}
}
```

### 3. Get Game State
```bash
curl "http://localhost:8090/game/{game_id}" \
  -H "Authorization: Bearer {access_token}"
```

### 4. Perform Actions
```bash
curl -X POST "http://localhost:8090/game/{game_id}/action" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {access_token}" \
  -d '{"action_type": "place_tiles", "tiles": ["tile-id-1", "tile-id-2", "tile-id-3"]}'
```

## Game Actions

### Available Actions:
- **`place_tiles`**: Place tiles from your hand onto the board
- **`draw_tile`**: Draw a tile from the pool (ends your turn)
- **`rearrange`**: Rearrange existing combinations on the board *(coming soon)*

## Testing

### Automated Tests
Run the test script to verify API functionality:

```bash
make test
```

Or run individual test files:
```bash
python tests/test_api.py          # Basic API functionality
python tests/test_actions.py      # Game actions and turns  
python tests/test_openapi.py      # OpenAPI specification validation
```

### Dependencies

The project uses minimal dependencies for optimal performance:

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | 0.116.1 | Web framework and API endpoints |
| `uvicorn` | 0.35.0 | ASGI server for running the application |
| `pydantic` | 2.11.9 | Data validation and JSON serialization |
| `pyjwt` | 2.10.1 | JWT token generation and validation |
| `python-multipart` | 0.0.6 | Form data parsing (FastAPI dependency) |
| `requests` | 2.32.5 | HTTP client for testing scripts |

## Game Flow

1. **Admin creates game** using basic auth credentials
2. **Players join** using game ID and choosing username (receive JWT token)
3. **Game starts** automatically when 2+ players join
4. **Players take turns** placing tiles or drawing from pool (using JWT token for authentication)
5. **First player** to empty their hand wins

## Project Structure

```
rummikub-backend/
├── main.py              # Entry point (imports from src/)
├── src/                 # Core application code
│   ├── __init__.py      # Package initialization  
│   ├── main.py          # FastAPI application
│   ├── models.py        # Pydantic models and data structures
│   └── game_service.py  # Game logic and business rules
├── scripts/             # Utility scripts
│   ├── generate_openapi.py # Script to generate OpenAPI specification
│   └── demo_multiscreen.py # Multi-screen demonstration script
├── tests/               # Test files
│   ├── test_api.py      # API testing script
│   ├── test_actions.py  # Game action tests
│   ├── test_openapi.py  # OpenAPI validation tests
│   ├── test_env_password.py # Environment password tests
│   ├── test_edge_cases.py # Edge case testing
│   └── test_multiscreen.py # Multi-screen testing
├── static/              # Static web files
│   ├── index.html       # Main web interface
│   └── rules.html       # Game rules page
├── openapi.json         # OpenAPI 3.1.0 specification (generated)
├── requirements.txt     # Python dependencies
├── Makefile            # Build automation and testing
├── Dockerfile          # Docker container configuration
├── docker-compose.yml  # Docker compose for easy deployment
├── RUMMIKUB_RULES.md   # Complete game rules
└── README.md           # This file
```

## Development

### Adding New Features
1. Update models in `src/models.py` if needed
2. Implement logic in `src/game_service.py`
3. Add API endpoints in `src/main.py`
4. Test with scripts in `tests/` directory

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## License

This project is for educational and demonstration purposes.

## Quick Reference Commands

```bash
# Local development
pip install -r requirements.txt && python main.py

# Docker development  
docker compose up --build

# Full test suite
make test

# API documentation
# Visit http://localhost:8090/docs (Swagger UI)
# Visit http://localhost:8090/redoc (ReDoc)

# Manual API testing
curl -u admin:admin -X POST localhost:8090/game -H "Content-Type: application/json" -d '{"max_players":2,"name":"TestHost"}'
```
