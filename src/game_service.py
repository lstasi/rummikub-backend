import random
import string
import threading
from typing import List, Optional, Dict
from .models import (
    Game, Player, Tile, TileColor, Combination, GameStatus, 
    PlayerStatus, GameState, GameAction, ActionResponse
)
from .redis_storage import RedisStorage


class GameService:
    def __init__(self):
        # Initialize Redis storage
        self.storage = RedisStorage()
        
        # Keep in-memory locks and counters for concurrency control
        self.game_locks: Dict[str, threading.Lock] = {}  # game_id -> lock for concurrency control
        self.action_counters: Dict[str, int] = {}  # game_id -> action counter for detecting race conditions

    def create_tile_pool(self) -> List[Tile]:
        """Create the initial pool of 106 tiles."""
        tiles = []
        
        # Create 104 numbered tiles (2 sets of 1-13 in each of 4 colors)
        for _ in range(2):
            for color in TileColor:
                for number in range(1, 14):
                    tiles.append(Tile(number=number, color=color))
        
        # Create 2 jokers
        tiles.extend([Tile(is_joker=True), Tile(is_joker=True)])
        
        # Shuffle the tiles
        random.shuffle(tiles)
        return tiles

    def _store_game(self, game: Game) -> bool:
        """Store a game in Redis."""
        return self.storage.set_json(f"game:{game.id}", game.model_dump())
    
    def _load_game(self, game_id: str) -> Optional[Game]:
        """Load a game from Redis."""
        game_data = self.storage.get_json(f"game:{game_id}")
        if game_data:
            return Game.model_validate(game_data)
        return None
    
    def _store_session(self, session_id: str, game_id: str, player_id: str) -> bool:
        """Store a session mapping in Redis."""
        return self.storage.set_json(f"session:{session_id}", {"game_id": game_id, "player_id": player_id})
    
    def _load_session(self, session_id: str) -> Optional[Dict[str, str]]:
        """Load a session mapping from Redis."""
        return self.storage.get_json(f"session:{session_id}")

    def generate_invite_code(self) -> str:
        """Generate a random 6-character invite code."""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    def create_game(self, max_players: int = 4, creator_name: str = "Admin") -> Game:
        """Create a new game."""
        game = Game(
            invite_code="",  # No longer used but keeping for compatibility
            tile_pool=self.create_tile_pool(),
            max_players=max_players
        )
        
        # Store game in Redis
        self._store_game(game)
        # Initialize concurrency control for this game
        self.game_locks[game.id] = threading.Lock()
        self.action_counters[game.id] = 0
        return game

    def find_game_by_invite_code(self, invite_code: str) -> Optional[Game]:
        """Find a game by its invite code."""
        # Get all game keys from Redis
        game_keys = self.storage.keys("game:*")
        for key in game_keys:
            game_data = self.storage.get_json(key)
            if game_data and game_data.get("invite_code") == invite_code:
                return Game.model_validate(game_data)
        return None

    def join_game_by_id(self, game_id: str, player_name: str = None) -> tuple[Optional[Game], Optional[Player], str]:
        """
        Join a game by game ID. Player names are auto-assigned as P1, P2, P3, P4.
        For multi-screen access: allows re-joining with same name if game is in progress.
        Returns (game, player, message)
        """
        game = self._load_game(game_id)
        if not game:
            return None, None, "Game not found"
        
        # If player_name is provided and game is in progress, allow re-join (multi-screen access)
        if player_name and game.status == GameStatus.IN_PROGRESS:
            existing_player = None
            for player in game.players:
                if player.name == player_name:
                    existing_player = player
                    break
            if existing_player:
                return game, existing_player, "Re-joined game for multi-screen access"
        
        # If game is finished, don't allow new joins
        if game.status == GameStatus.FINISHED:
            return None, None, "Game has finished"
        
        # For waiting games, auto-assign player names
        if game.status == GameStatus.WAITING:
            if len(game.players) >= game.max_players:
                return None, None, "Game is full"
            
            # Auto-assign player name as P1, P2, P3, P4
            auto_name = f"P{len(game.players) + 1}"
            
            # Create new player with auto-assigned name
            player = Player(name=auto_name)
            
            # Deal 14 tiles to the player
            if len(game.tile_pool) >= 14:
                player.tiles = game.tile_pool[:14]
                game.tile_pool = game.tile_pool[14:]
            else:
                return None, None, "Not enough tiles in pool"
            
            game.players.append(player)
            
            # Start game if we have at least 2 players
            if len(game.players) >= 2:
                game.status = GameStatus.IN_PROGRESS
                for p in game.players:
                    p.status = PlayerStatus.PLAYING
            
            # Save updated game to Redis
            self._store_game(game)
            return game, player, "Successfully joined game"
        
        return None, None, "Unable to join game"

    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        session_id = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        # Check Redis for session existence
        while self.storage.exists(f"session:{session_id}"):
            session_id = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        return session_id

    def get_game_state_by_player(self, game_id: str, player_id: str) -> Optional[GameState]:
        """Get game state for a specific player by player ID."""
        game = self._load_game(game_id)
        if not game:
            return None
        
        player = self._get_player_by_id(game, player_id)
        if not player:
            return None
        
        # Build player info (without tiles)
        players_info = []
        for p in game.players:
            players_info.append({
                "name": p.name,
                "status": p.status,
                "tile_count": len(p.tiles),
                "has_initial_meld": p.has_initial_meld
            })
        
        return GameState(
            game_id=game.id,
            status=game.status,
            players=players_info,
            your_tiles=player.tiles,
            board=game.board,
            current_player=game.current_player.name if game.current_player else None,
            can_play=game.current_player.id == player.id if game.current_player else False
        )

    def _get_player_by_id(self, game: Game, player_id: str) -> Optional[Player]:
        """Get a player by their ID."""
        for player in game.players:
            if player.id == player_id:
                return player
        return None

    def perform_action_by_player(self, game_id: str, player_id: str, action: GameAction, session_id: str = None) -> ActionResponse:
        """Perform a game action by player ID with concurrency control for multi-screen access."""
        game = self._load_game(game_id)
        if not game:
            return ActionResponse(success=False, message="Game not found")
        
        # Get the game lock for concurrency control
        game_lock = self.game_locks.get(game_id)
        if not game_lock:
            return ActionResponse(success=False, message="Game lock not found")
        
        # Use lock to prevent race conditions between multiple sessions
        with game_lock:
            # Re-check game state after acquiring lock (it might have changed)
            game = self._load_game(game_id)
            if not game:
                return ActionResponse(success=False, message="Game not found")
            
            player = self._get_player_by_id(game, player_id)
            if not player:
                return ActionResponse(success=False, message="Player not found")
            
            if game.status != GameStatus.IN_PROGRESS:
                return ActionResponse(success=False, message="Game is not in progress")
            
            if game.current_player.id != player.id:
                return ActionResponse(success=False, message="Not your turn")
            
            # Increment action counter to track when actions are processed
            self.action_counters[game_id] += 1
            
            # Handle different action types
            if action.action_type == "place_tiles":
                return self._handle_place_tiles(game, player, action, session_id)
            elif action.action_type == "draw_tile":
                return self._handle_draw_tile(game, player, session_id)
            elif action.action_type == "rearrange":
                return self._handle_rearrange(game, player, action, session_id)
            else:
                return ActionResponse(success=False, message="Invalid action type")

    def _handle_place_tiles(self, game: Game, player: Player, action: GameAction, session_id: str = None) -> ActionResponse:
        """Handle placing tiles on the board."""
        if not action.tiles:
            return ActionResponse(success=False, message="No tiles specified")
        
        # Find the tiles in player's hand
        tiles_to_place = []
        for tile_id in action.tiles:
            tile = self._find_tile_by_id(player.tiles, tile_id)
            if not tile:
                return ActionResponse(success=False, message=f"Tile {tile_id} not found in hand")
            tiles_to_place.append(tile)
        
        # Create combination and validate
        combination = Combination(tiles=tiles_to_place)
        if not combination.is_valid():
            return ActionResponse(success=False, message="Invalid tile combination")
        
        # Check initial meld requirement (30 points minimum)
        if not player.has_initial_meld:
            total_value = sum(combo.get_value() for combo in game.board if any(
                tile.id in [t.id for t in combo.tiles] for tile in tiles_to_place
            )) + combination.get_value()
            
            if total_value < 30:
                return ActionResponse(success=False, message="Initial meld must be worth at least 30 points")
            
            player.has_initial_meld = True
        
        # Remove tiles from player's hand and add combination to board
        for tile in tiles_to_place:
            player.tiles.remove(tile)
        
        game.board.append(combination)
        
        # Check win condition
        if len(player.tiles) == 0:
            player.status = PlayerStatus.FINISHED
            game.status = GameStatus.FINISHED
        else:
            game.next_turn()
        
        # Save updated game to Redis
        self._store_game(game)
        
        game_state = self.get_game_state_by_player(game.id, player.id)
        return ActionResponse(
            success=True, 
            message="Tiles placed successfully",
            game_state=game_state
        )

    def _handle_draw_tile(self, game: Game, player: Player, session_id: str = None) -> ActionResponse:
        """Handle drawing a tile from the pool."""
        if len(game.tile_pool) == 0:
            return ActionResponse(success=False, message="No tiles left in pool")
        
        # Draw a tile
        drawn_tile = game.tile_pool.pop(0)
        player.tiles.append(drawn_tile)
        
        # End turn
        game.next_turn()
        
        # Save updated game to Redis
        self._store_game(game)
        
        game_state = self.get_game_state_by_player(game.id, player.id)
        return ActionResponse(
            success=True,
            message="Tile drawn successfully",
            game_state=game_state
        )

    def _handle_rearrange(self, game: Game, player: Player, action: GameAction, session_id: str = None) -> ActionResponse:
        """Handle rearranging tiles on the board."""
        # This is a complex operation that would involve validating that all
        # combinations remain valid after rearrangement
        # For now, return a not implemented message
        return ActionResponse(
            success=False,
            message="Rearrange action not yet implemented"
        )

    def _find_tile_by_id(self, tiles: List[Tile], tile_id: str) -> Optional[Tile]:
        """Find a tile by its ID in a list of tiles."""
        for tile in tiles:
            if tile.id == tile_id:
                return tile
        return None

    def get_game_by_id(self, game_id: str) -> Optional[Game]:
        """Get a game by its ID."""
        return self._load_game(game_id)

    def validate_session(self, session_id: str) -> Optional[Dict[str, str]]:
        """Validate a session and return session info."""
        return self._load_session(session_id)
    
    def list_all_games(self) -> List[Dict[str, any]]:
        """List all existing games with basic information."""
        game_keys = self.storage.keys("game:*")
        games_info = []
        
        for key in game_keys:
            try:
                game = self._load_game(key.replace("game:", ""))
                if game:
                    games_info.append({
                        "game_id": game.id,
                        "status": game.status,
                        "players": [{"name": p.name, "status": p.status} for p in game.players],
                        "player_count": len(game.players),
                        "max_players": game.max_players,
                        "invite_code": game.invite_code
                    })
            except Exception as e:
                # Skip invalid games
                continue
                
        return games_info