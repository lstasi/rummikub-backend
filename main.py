from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Optional
import secrets
from models import (
    CreateGameRequest, JoinGameRequest, GameAction, 
    ActionResponse, GameState, Game
)
from game_service import GameService

app = FastAPI(title="Rummikub Backend API", version="1.0.0")
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


@app.get("/")
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


@app.post("/game")
async def create_game(
    request: CreateGameRequest,
    credentials: HTTPBasicCredentials = Depends(verify_admin_credentials)
):
    """
    Create a new game. Requires authentication.
    Returns game ID and invite code.
    """
    game = game_service.create_game(request.max_players)
    
    return {
        "game_id": game.id,
        "invite_code": game.invite_code,
        "max_players": game.max_players,
        "status": game.status,
        "message": "Game created successfully"
    }


@app.post("/game/{game_id}/join")
async def join_game(game_id: str, request: JoinGameRequest):
    """
    Join a game using invite code and player name.
    Returns session ID for subsequent requests.
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


@app.get("/game/{game_id}")
async def get_game_state(game_id: str, session_id: str):
    """
    Get current game state. Requires session ID.
    Returns game state with only the requesting player's tiles.
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


@app.post("/game/{game_id}/action")
async def perform_action(game_id: str, session_id: str, action: GameAction):
    """
    Perform a game action. Requires session ID.
    Available actions: place_tiles, draw_tile, rearrange
    """
    # Validate session
    session_info = game_service.validate_session(session_id)
    if not session_info:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    result = game_service.perform_action(game_id, session_id, action)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    
    return result


@app.get("/game/{game_id}/info")
async def get_game_info(game_id: str):
    """
    Get basic game information (no session required).
    Useful for checking if a game exists and its status.
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