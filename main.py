from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Optional
import secrets
from models import (
    CreateGameRequest, JoinGameRequest, GameAction, 
    ActionResponse, GameState, Game
)
from game_service import GameService

app = FastAPI(
    title="Rummikub Backend API",
    version="1.0.0",
    description="""
A Python-based REST API for playing Rummikub online. This backend provides game logic, 
session management, and all necessary endpoints to play Rummikub without requiring user registration.

## Features
- Complete Rummikub game logic implementation
- Session-based authentication (no user registration required)
- Invite code system for joining games
- In-memory database for fast gameplay
- RESTful API with comprehensive game state management

## Authentication
Game creation requires basic authentication:
- Username: `admin`
- Password: `rummikub2024`

All other game operations use session-based authentication with session IDs.
""",
    contact={
        "name": "Rummikub Backend API",
        "url": "https://github.com/lstasi/rummikub-backend",
    },
    license_info={
        "name": "MIT License",
    },
    openapi_tags=[
        {
            "name": "general",
            "description": "General API information and health checks",
        },
        {
            "name": "game-management",
            "description": "Game creation and basic game information",
        },
        {
            "name": "game-play",
            "description": "Player actions and game state management",
        },
    ]
)
security = HTTPBasic()
game_service = GameService()

# Hard-coded credentials for game creation
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "rummikub2024"


def verify_admin_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify admin credentials for game creation."""
    is_correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    is_correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials


@app.get("/", tags=["general"])
async def root():
    """Root endpoint with basic API information."""
    return {
        "message": "Rummikub Backend API",
        "version": "1.0.0",
        "endpoints": {
            "create_game": "POST /game (requires auth)",
            "join_game": "POST /game/{game_id}/join",
            "get_game_state": "GET /game/{game_id}",
            "perform_action": "POST /game/{game_id}/action"
        }
    }


@app.post("/game", tags=["game-management"])
async def create_game(
    request: CreateGameRequest,
    credentials: HTTPBasicCredentials = Depends(verify_admin_credentials)
):
    """
    Create a new game. Requires authentication.
    
    Returns game ID and invite code that players can use to join the game.
    The game will be in 'waiting' status until players join.
    
    **Authentication Required**: Basic Auth (admin:rummikub2024)
    """
    game = game_service.create_game(request.max_players)
    
    return {
        "game_id": game.id,
        "invite_code": game.invite_code,
        "max_players": game.max_players,
        "status": game.status,
        "message": "Game created successfully"
    }


@app.post("/game/{game_id}/join", tags=["game-play"])
async def join_game(game_id: str, request: JoinGameRequest):
    """
    Join a game using invite code and player name.
    
    Returns session ID for subsequent requests. The session ID must be used
    in all future API calls to identify the player.
    
    The game will automatically start when 2 or more players have joined.
    """
    game, session_id, message = game_service.join_game(
        request.invite_code, 
        request.player_name
    )
    
    if not game:
        raise HTTPException(status_code=400, detail=message)
    
    if game.id != game_id:
        raise HTTPException(status_code=400, detail="Game ID does not match invite code")
    
    return {
        "session_id": session_id,
        "game_id": game.id,
        "message": message,
        "game_state": game_service.get_game_state(game.id, session_id)
    }


@app.get("/game/{game_id}", tags=["game-play"])
async def get_game_state(game_id: str, session_id: str):
    """
    Get current game state. Requires session ID.
    
    Returns game state with only the requesting player's tiles visible.
    Other players' tiles counts are shown but not the actual tiles.
    
    **Authentication Required**: Session ID (obtained from joining a game)
    """
    # Validate session
    session_info = game_service.validate_session(session_id)
    if not session_info:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    if session_info["game_id"] != game_id:
        raise HTTPException(status_code=400, detail="Session does not match game")
    
    game_state = game_service.get_game_state(game_id, session_id)
    if not game_state:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return game_state


@app.post("/game/{game_id}/action", tags=["game-play"])
async def perform_action(game_id: str, session_id: str, action: GameAction):
    """
    Perform a game action. Requires session ID.
    
    **Available Actions:**
    - `place_tiles`: Place tiles from your hand onto the board in new combinations
    - `draw_tile`: Draw a tile from the pool (ends your turn)
    - `rearrange`: Rearrange existing combinations on the board (coming soon)
    
    **Authentication Required**: Session ID (obtained from joining a game)
    
    **Note**: You can only perform actions during your turn.
    """
    # Validate session
    session_info = game_service.validate_session(session_id)
    if not session_info:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    result = game_service.perform_action(game_id, session_id, action)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    
    return result


@app.get("/game/{game_id}/info", tags=["game-management"])
async def get_game_info(game_id: str):
    """
    Get basic game information (no session required).
    
    Useful for checking if a game exists, its status, and who has joined.
    This endpoint doesn't require authentication and can be used to verify
    a game ID before attempting to join.
    """
    game = game_service.get_game_by_id(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return {
        "game_id": game.id,
        "status": game.status,
        "player_count": len(game.players),
        "max_players": game.max_players,
        "created_at": game.created_at,
        "players": [{"name": p.name, "status": p.status} for p in game.players]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)