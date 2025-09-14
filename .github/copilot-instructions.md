# Rummikub Backend API

A Python FastAPI backend for playing Rummikub online with session-based authentication, in-memory game state, and Docker deployment support.

**Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.**

## Working Effectively

### Local Development Setup
- **Install dependencies:**
  - `pip install -r requirements.txt` -- takes ~10 seconds. NEVER CANCEL.
- **Start the server:**
  - `python main.py` -- starts immediately (~1-2 seconds)
  - Server runs on `http://0.0.0.0:8090` (accessible via `http://localhost:8090`)
- **Stop the server:**
  - Press `Ctrl+C` in the terminal

### Docker Development (Recommended)
- **Build and start:**
  - `docker compose build` -- takes ~17 seconds first time. NEVER CANCEL. Set timeout to 60+ seconds.
  - `docker compose up` -- starts immediately after build
  - **Note:** Ignore the warning about obsolete `version` attribute in docker-compose.yml (harmless)
- **Stop Docker:**
  - `docker compose down` or `Ctrl+C`

### Testing and Validation
- **Run API tests:**
  - `python test_api.py` -- takes ~0.1 seconds. Tests basic API functionality.
  - `python test_actions.py` -- takes ~0.1 seconds. Tests game actions and turns.
  - `python test_openapi.py` -- takes ~0.02 seconds. Validates OpenAPI specification.
- **Generate OpenAPI spec:**
  - `python generate_openapi.py` -- takes ~0.5 seconds. Updates openapi.json file.
- **Syntax validation:**
  - `python -m py_compile *.py` -- validates all Python files compile correctly

## Validation Scenarios

**ALWAYS run through these scenarios after making changes:**

### 1. Basic API Test
```bash
python test_api.py
```
Should output "🎉 All tests completed!" and test: root endpoint, game creation, joining, state retrieval.

### 2. Game Flow Test  
```bash
python test_actions.py
```
Should test: game creation, 2 players joining, game starting, turn-based actions, invalid action rejection.

### 3. Manual Game Flow (Complete End-to-End)
1. **Start server:** `python main.py` or `docker compose up`
2. **Create game:** 
   ```bash
   curl -X POST "http://localhost:8090/game" \
     -H "Content-Type: application/json" \
     -u "admin:rummikub2024" \
     -d '{"max_players": 4}'
   ```
3. **Join game:** Use the returned invite_code in:
   ```bash
   curl -X POST "http://localhost:8090/game/{game_id}/join" \
     -H "Content-Type: application/json" \
     -d '{"invite_code": "INVITE_CODE", "player_name": "TestPlayer"}'
   ```
4. **Test game state:** Use session_id from join response:
   ```bash
   curl "http://localhost:8090/game/{game_id}?session_id={session_id}"
   ```
5. **Verify documentation:** Visit `http://localhost:8090/docs` for Swagger UI

## Project Structure and Navigation

### Key Files
- **`main.py`** - FastAPI application with all API endpoints
- **`models.py`** - Pydantic models for game data structures (Tile, Player, Game, etc.)
- **`game_service.py`** - Core game logic and business rules  
- **`test_*.py`** - Comprehensive test suites
- **`requirements.txt`** - Python dependencies (only 4 packages)
- **`Dockerfile` + `docker-compose.yml`** - Container deployment
- **`RUMMIKUB_RULES.md`** - Complete game rules reference

### Code Organization
```
rummikub-backend/
├── main.py              # 🚀 FastAPI app & endpoints
├── models.py            # 📊 Data models (Tile, Game, Player)  
├── game_service.py      # 🎲 Game logic & rules engine
├── test_api.py         # ✅ Basic API functionality tests
├── test_actions.py     # ✅ Game action & turn tests  
├── test_openapi.py     # ✅ OpenAPI spec validation
├── generate_openapi.py  # 📋 OpenAPI spec generator
├── openapi.json         # 📄 Generated API specification
├── requirements.txt     # 📦 Python dependencies
├── Dockerfile          # 🐳 Container build config
├── docker-compose.yml  # 🐳 Container orchestration
├── RUMMIKUB_RULES.md   # 📖 Game rules documentation
└── README.md           # 📘 Project documentation
```

## Game Logic and API

### Authentication
- **Game Creation:** Basic Auth with `admin:rummikub2024`
- **All Other Operations:** Session-based with session_id

### Core Game Flow
1. Admin creates game → Returns game_id and invite_code
2. Players join with invite_code → Game starts when 2+ players join
3. Players take turns: place tiles OR draw tile (ends turn)
4. First player to empty their hand wins

### Key API Endpoints
- `GET /` - API info
- `POST /game` - Create game (requires admin auth)
- `POST /game/{game_id}/join` - Join with invite code  
- `GET /game/{game_id}` - Get game state (requires session_id)
- `POST /game/{game_id}/action` - Perform game action (requires session_id)
- `GET /docs` - Swagger UI documentation

## Common Development Tasks

### Adding New Game Features
1. **Update models:** Add/modify classes in `models.py` 
2. **Implement logic:** Add business rules in `game_service.py`
3. **Add endpoints:** Create API routes in `main.py`
4. **Test functionality:** Run all test scripts to verify
5. **Always validate:** Run complete end-to-end scenario

### Debugging Game Issues
1. **Check game state:** Use `GET /game/{game_id}` endpoint
2. **Review game logic:** Most rules are in `GameService` class
3. **Test with curl:** Use manual API calls to isolate issues
4. **Check tile validation:** Combination logic is in `Combination.is_valid()`

### API Changes
1. **Update endpoints:** Modify FastAPI routes in `main.py`
2. **Update models:** Ensure request/response models match in `models.py`  
3. **Regenerate spec:** Run `python generate_openapi.py`
4. **Validate spec:** Run `python test_openapi.py`
5. **Test endpoints:** Use `test_api.py` and manual curl commands

## Important Notes

### Game State Management
- **In-memory storage:** All game state lost on server restart
- **Session-based:** Each player gets unique session_id for API calls
- **Real-time:** No WebSocket support - use polling for live updates

### Development Constraints  
- **No database:** Uses in-memory dictionaries for game storage
- **No user accounts:** Players identified by session_id only
- **Single instance:** No horizontal scaling support

### Known Issues and Warnings
- **Docker compose version warning:** Harmless, can be ignored
- **Server binds 0.0.0.0:8090:** Accessible from any interface  
- **No persistence:** Game state lost on restart
- **Hard-coded credentials:** Admin credentials in source code

## Testing Strategy

**ALWAYS run ALL tests after making changes:**

```bash
# Fast validation suite (< 1 second total)
python -m py_compile *.py        # Syntax validation
python test_openapi.py           # OpenAPI spec validation  
python test_api.py              # Basic API functionality
python test_actions.py          # Game action testing

# OpenAPI regeneration (if models changed)
python generate_openapi.py      # Updates openapi.json

# Manual end-to-end validation
# 1. Start server: python main.py
# 2. Create game with admin credentials  
# 3. Join game with test player
# 4. Verify game state and actions work
# 5. Test invalid actions are rejected
```

## Troubleshooting

### Server Won't Start
- **Check port 8090:** Kill any processes using the port
- **Verify dependencies:** Run `pip install -r requirements.txt`
- **Check syntax:** Run `python -m py_compile main.py`

### Tests Failing  
- **Ensure server running:** Tests expect server on localhost:8090
- **Check dependencies:** Ensure `requests` module available (usually pre-installed)
- **Review error messages:** Test scripts provide detailed error output

### Docker Issues
- **Build failures:** Check Docker daemon is running  
- **Port conflicts:** Ensure port 8090 is available
- **Version warnings:** Safe to ignore obsolete version attribute warning

## Quick Reference Commands

```bash
# Local development
pip install -r requirements.txt && python main.py

# Docker development  
docker compose build && docker compose up

# Full test suite
python test_api.py && python test_actions.py && python test_openapi.py

# API documentation
# Visit http://localhost:8090/docs (Swagger UI)
# Visit http://localhost:8090/redoc (ReDoc)

# Manual API testing
curl -u admin:rummikub2024 -X POST localhost:8090/game -H "Content-Type: application/json" -d '{"max_players":2}'
```