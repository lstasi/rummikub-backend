from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid
from datetime import datetime


class TileColor(str, Enum):
    BLACK = "black"
    RED = "red"
    BLUE = "blue"
    ORANGE = "orange"


class Tile(BaseModel):
    number: Optional[int] = None  # None for jokers
    color: Optional[TileColor] = None  # None for jokers
    is_joker: bool = False
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    @property
    def value(self) -> int:
        """Get the point value of the tile."""
        if self.is_joker:
            return 0  # Joker value depends on context
        return self.number or 0

    def __str__(self) -> str:
        if self.is_joker:
            return "J"
        return f"{self.number}{self.color[0].upper()}"


class Combination(BaseModel):
    tiles: List[Tile]
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    def is_valid(self) -> bool:
        """Check if the combination is valid (group or run)."""
        if len(self.tiles) < 3:
            return False
        
        # Handle jokers by trying different values
        return self._is_valid_group() or self._is_valid_run()

    def _is_valid_group(self) -> bool:
        """Check if tiles form a valid group (same number, different colors)."""
        if len(self.tiles) > 4:
            return False
            
        numbers = set()
        colors = set()
        
        for tile in self.tiles:
            if not tile.is_joker:
                numbers.add(tile.number)
                colors.add(tile.color)
        
        # All non-joker tiles should have same number and different colors
        return len(numbers) <= 1 and len(colors) == len([t for t in self.tiles if not t.is_joker])

    def _is_valid_run(self) -> bool:
        """Check if tiles form a valid run (consecutive numbers, same color)."""
        colors = set()
        numbers = []
        
        for tile in self.tiles:
            if not tile.is_joker:
                colors.add(tile.color)
                numbers.append(tile.number)
        
        # All non-joker tiles should have same color
        if len(colors) > 1:
            return False
            
        if not numbers:  # All jokers
            return True
            
        numbers.sort()
        # Check if numbers are consecutive (accounting for jokers)
        return self._can_form_sequence(numbers, len(self.tiles))

    def _can_form_sequence(self, numbers: List[int], total_tiles: int) -> bool:
        """Check if numbers can form a sequence with jokers filling gaps."""
        if not numbers:
            return True
            
        min_num, max_num = min(numbers), max(numbers)
        expected_length = max_num - min_num + 1
        
        # Check if we have enough tiles to fill the sequence
        return expected_length <= total_tiles and expected_length >= 3

    def get_value(self) -> int:
        """Get total value of the combination."""
        return sum(tile.value for tile in self.tiles)


class PlayerStatus(str, Enum):
    WAITING = "waiting"
    PLAYING = "playing"
    FINISHED = "finished"


class Player(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    tiles: List[Tile] = []
    status: PlayerStatus = PlayerStatus.WAITING
    session_id: Optional[str] = None
    has_initial_meld: bool = False


class GameStatus(str, Enum):
    WAITING = "waiting"  # Waiting for players to join
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"


class Game(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    invite_code: str
    status: GameStatus = GameStatus.WAITING
    players: List[Player] = []
    board: List[Combination] = []
    tile_pool: List[Tile] = []
    current_player_index: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    max_players: int = 4

    @property
    def current_player(self) -> Optional[Player]:
        if not self.players or self.current_player_index >= len(self.players):
            return None
        return self.players[self.current_player_index]

    def next_turn(self):
        """Move to the next player's turn."""
        if self.players:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)


class GameState(BaseModel):
    game_id: str
    status: GameStatus
    players: List[Dict[str, Any]]  # Player info without tiles
    your_tiles: List[Tile]  # Only the requesting player's tiles
    board: List[Combination]
    current_player: Optional[str]  # Player name
    can_play: bool  # Whether it's your turn


class JoinGameRequest(BaseModel):
    invite_code: str
    player_name: str


class CreateGameRequest(BaseModel):
    max_players: int = Field(default=4, ge=2, le=4)


class GameAction(BaseModel):
    action_type: str  # "place_tiles", "rearrange", "draw_tile"
    tiles: Optional[List[str]] = None  # Tile IDs
    combinations: Optional[List[List[str]]] = None  # For rearranging
    target_combination_id: Optional[str] = None


class ActionResponse(BaseModel):
    success: bool
    message: str
    game_state: Optional[GameState] = None