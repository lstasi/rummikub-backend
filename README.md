# Rummikub Backend API

A Python-based REST API for playing Rummikub online. This backend provides game logic, session management, and all necessary endpoints to play Rummikub without requiring user registration.

## Features

- 🎮 Complete Rummikub game logic implementation
- 🔐 Session-based authentication (no user registration required)
- 🎫 Invite code system for joining games
- 🏗️ In-memory database for fast gameplay
- 🐳 Docker support for easy deployment
- 📋 RESTful API with comprehensive game state management

## Game Rules

See [RUMMIKUB_RULES.md](RUMMIKUB_RULES.md) for complete game rules and gameplay instructions.

## API Documentation

### OpenAPI Specification
A complete OpenAPI 3.1.0 specification is available in the repository:
- **Static file**: [`openapi.json`](openapi.json) - Version-controlled OpenAPI specification
- **Live documentation**: Available when server is running:
  - Swagger UI: `http://localhost:8000/docs`
  - ReDoc: `http://localhost:8000/redoc`
  - OpenAPI JSON: `http://localhost:8000/openapi.json`

To regenerate the OpenAPI specification file:
```bash
python generate_openapi.py
```

## API Endpoints

### Authentication
- **Game Creation**: Requires basic auth with hard-coded credentials
  - Username: `admin`
  - Password: `rummikub2024`

### Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | API information | No |
| POST | `/game` | Create new game | Yes (Basic Auth) |
| POST | `/game/{game_id}/join` | Join game with invite code | No |
| GET | `/game/{game_id}` | Get game state | Session ID |
| POST | `/game/{game_id}/action` | Perform game action | Session ID |
| GET | `/game/{game_id}/info` | Get basic game info | No |

## Quick Start

### Using Docker (Recommended)

1. **Clone and build:**
   ```bash
   git clone <repository-url>
   cd rummikub-backend
   docker-compose up --build
   ```

2. **API will be available at:** `http://localhost:8000`

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the server:**
   ```bash
   python main.py
   ```

3. **API will be available at:** `http://localhost:8000`

## Usage Example

### 1. Create a Game
```bash
curl -X POST "http://localhost:8000/game" \
  -H "Content-Type: application/json" \
  -u "admin:rummikub2024" \
  -d '{"max_players": 4}'
```

Response:
```json
{
  "game_id": "game-uuid",
  "invite_code": "ABC123",
  "max_players": 4,
  "status": "waiting",
  "message": "Game created successfully"
}
```

### 2. Join a Game
```bash
curl -X POST "http://localhost:8000/game/{game_id}/join" \
  -H "Content-Type: application/json" \
  -d '{"invite_code": "ABC123", "player_name": "PlayerName"}'
```

Response:
```json
{
  "session_id": "session-uuid",
  "game_id": "game-uuid",
  "message": "Successfully joined game",
  "game_state": {...}
}
```

### 3. Get Game State
```bash
curl "http://localhost:8000/game/{game_id}?session_id={session_id}"
```

### 4. Perform Actions
```bash
curl -X POST "http://localhost:8000/game/{game_id}/action?session_id={session_id}" \
  -H "Content-Type: application/json" \
  -d '{"action_type": "place_tiles", "tiles": ["tile-id-1", "tile-id-2", "tile-id-3"]}'
```

## Game Actions

### Available Actions:
- **`place_tiles`**: Place tiles from your hand onto the board
- **`draw_tile`**: Draw a tile from the pool (ends your turn)
- **`rearrange`**: Rearrange existing combinations on the board *(coming soon)*

## Testing

Run the test script to verify API functionality:

```bash
python test_api.py
```

## Game Flow

1. **Admin creates game** using basic auth
2. **Players join** using invite code and choose username
3. **Game starts** automatically when 2+ players join
4. **Players take turns** placing tiles or drawing from pool
5. **First player** to empty their hand wins

## Project Structure

```
rummikub-backend/
├── main.py              # FastAPI application
├── models.py            # Pydantic models and data structures
├── game_service.py      # Game logic and business rules
├── test_api.py         # API testing script
├── generate_openapi.py  # Script to generate OpenAPI specification
├── openapi.json         # OpenAPI 3.1.0 specification (generated)
├── requirements.txt     # Python dependencies
├── Dockerfile          # Docker container configuration
├── docker-compose.yml  # Docker compose for easy deployment
├── RUMMIKUB_RULES.md   # Complete game rules
└── README.md           # This file
```

## Development

### Adding New Features
1. Update models in `models.py` if needed
2. Implement logic in `game_service.py`
3. Add API endpoints in `main.py`
4. Test with `test_api.py`

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## License

This project is for educational and demonstration purposes.
