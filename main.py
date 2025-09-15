from fastapi import FastAPI, HTTPException, Depends, status, Header
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import Optional
import secrets
import jwt
from datetime import datetime, timedelta
import os
import logging

# Configure enhanced logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

security = HTTPBasic()
game_service = GameService()

# Hard-coded credentials for game creation
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "rummikub2024")
JWT_SECRET = "rummikub-jwt-secret-2024"
JWT_ALGORITHM = "HS256"

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


def create_access_token(game_id: str, player_id: str, player_name: str) -> str:
    """Create a JWT access token for a player with unique session ID for multi-screen access."""
    import uuid
    session_id = str(uuid.uuid4())  # Unique session ID for each login
    payload = {
        "game_id": game_id,
        "player_id": player_id,
        "player_name": player_name,
        "session_id": session_id,  # Add session ID to make tokens unique
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(authorization: str = Header(...)):
    """Verify and decode JWT token from Authorization header."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected 'Bearer <token>'"
        )
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


@app.get("/", tags=["general"], response_class=HTMLResponse)
async def root():
    """Serve the main web interface."""
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse("""
        <html>
        <head><title>Rummikub Backend</title></head>
        <body>
        <h1>Rummikub Backend API</h1>
        <p>The web interface is not available. API endpoints are still accessible.</p>
        <p><a href="/docs">API Documentation</a></p>
        </body>
        </html>
        """, status_code=200)


@app.post("/game", tags=["game-management"])
async def create_game(
    request: CreateGameRequest,
    credentials: HTTPBasicCredentials = Depends(verify_admin_credentials)
):
    """
    Create a new game. Requires authentication.
    
    Returns game ID that players can use to join the game.
    The game will be in 'waiting' status until players join.
    
    **Authentication Required**: Basic Auth (admin:rummikub2024)
    """
    logger.info(f"Creating new game for creator: {request.name}, max_players: {request.max_players}")
    game = game_service.create_game(request.max_players, request.name)
    logger.info(f"Game created successfully with ID: {game.id}")
    
    return {
        "game_id": game.id,
        "max_players": game.max_players,
        "creator_name": request.name,
        "status": game.status,
        "message": "Game created successfully"
    }


@app.post("/game/{game_id}/join", tags=["game-play"])
async def join_game(game_id: str, request: JoinGameRequest):
    """
    Join a game using game ID and player name.
    
    Returns access token for subsequent requests. The access token must be used
    in all future API calls as a Bearer token in the Authorization header.
    
    The game will automatically start when 2 or more players have joined.
    """
    logger.info(f"Player '{request.player_name}' attempting to join game: {game_id}")
    game, player, message = game_service.join_game_by_id(
        game_id, 
        request.player_name
    )
    
    if not game:
        logger.warning(f"Failed to join game {game_id}: {message}")
        raise HTTPException(status_code=400, detail=message)
    
    logger.info(f"Player '{player.name}' successfully joined game {game_id}")
    
    # Create JWT token
    access_token = create_access_token(game.id, player.id, player.name)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "game_id": game.id,
        "player_name": player.name,
        "message": message,
        "game_state": game_service.get_game_state_by_player(game.id, player.id)
    }


@app.get("/game/{game_id}", tags=["game-play"])
async def get_game_state(game_id: str, token_data: dict = Depends(verify_token)):
    """
    Get current game state. Requires Bearer token.
    
    Returns game state with only the requesting player's tiles visible.
    Other players' tiles counts are shown but not the actual tiles.
    
    **Authentication Required**: Bearer token (obtained from joining a game)
    """
    if token_data["game_id"] != game_id:
        raise HTTPException(status_code=400, detail="Token does not match game")
    
    game_state = game_service.get_game_state_by_player(game_id, token_data["player_id"])
    if not game_state:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return game_state


@app.post("/game/{game_id}/action", tags=["game-play"])
async def perform_action(game_id: str, action: GameAction, token_data: dict = Depends(verify_token)):
    """
    Perform a game action. Requires Bearer token.
    
    **Available Actions:**
    - `place_tiles`: Place tiles from your hand onto the board in new combinations
    - `draw_tile`: Draw a tile from the pool (ends your turn)
    - `rearrange`: Rearrange existing combinations on the board (coming soon)
    
    **Authentication Required**: Bearer token (obtained from joining a game)
    
    **Note**: You can only perform actions during your turn.
    """
    if token_data["game_id"] != game_id:
        raise HTTPException(status_code=400, detail="Token does not match game")
    
    result = game_service.perform_action_by_player(
        game_id, 
        token_data["player_id"], 
        action, 
        token_data.get("session_id")
    )
    
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
    logger.info("Starting Rummikub Backend API server...")
    logger.info("Server will be available at: http://localhost:8090")
    logger.info("API documentation: http://localhost:8090/docs")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8090,
        log_level="debug",
        access_log=True
    )