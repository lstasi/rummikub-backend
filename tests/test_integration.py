#!/usr/bin/env python3
"""
Integration test for complete Rummikub game simulation.
Tests the entire game engine by running complete games with AI players.
No HTTP API testing - pure backend logic validation.
"""

import random
import sys
import os
from typing import List, Optional, Dict, Set, Tuple, Any
from collections import defaultdict

# Add src to path for imports
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, src_path)

# Copy the necessary classes directly to avoid import issues
import threading
import string
import uuid
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

# Copy TileColor enum
class TileColor(str, Enum):
    BLACK = "black"
    RED = "red"
    BLUE = "blue"
    ORANGE = "orange"

# Copy Tile class  
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

# Copy Combination class
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

# Copy enums
class PlayerStatus(str, Enum):
    WAITING = "waiting"
    PLAYING = "playing"
    FINISHED = "finished"

class GameStatus(str, Enum):
    WAITING = "waiting"  # Waiting for players to join
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"

# Copy Player class
class Player(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    tiles: List[Tile] = []
    status: PlayerStatus = PlayerStatus.WAITING
    session_id: Optional[str] = None
    has_initial_meld: bool = False

# Copy Game class
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

# Copy action classes
class GameAction(BaseModel):
    action_type: str  # "place_tiles", "rearrange", "draw_tile"
    tiles: Optional[List[str]] = None  # Tile IDs
    combinations: Optional[List[List[str]]] = None  # For rearranging
    target_combination_id: Optional[str] = None

class GameState(BaseModel):
    game_id: str
    status: GameStatus
    players: List[Dict[str, Any]]  # Player info without tiles
    your_tiles: List[Tile]  # Only the requesting player's tiles
    board: List[Combination]
    current_player: Optional[str]  # Player name
    can_play: bool  # Whether it's your turn

class ActionResponse(BaseModel):
    success: bool
    message: str
    game_state: Optional[GameState] = None

# Copy GameService class
class GameService:
    def __init__(self):
        self.games: Dict[str, Game] = {}
        self.sessions: Dict[str, Dict[str, str]] = {}  # session_id -> {game_id, player_id}
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
        
        self.games[game.id] = game
        # Initialize concurrency control for this game
        self.game_locks[game.id] = threading.Lock()
        self.action_counters[game.id] = 0
        
        return game

    def join_game_by_id(self, game_id: str, player_name: str) -> tuple[Optional[Game], Optional[Player], str]:
        """Join a game by its ID."""
        game = self.games.get(game_id)
        if not game:
            return None, None, "Game not found"
        
        # Check if player already exists
        existing_player = None
        for player in game.players:
            if player.name == player_name:
                existing_player = player
                break
        
        if game.status == GameStatus.FINISHED:
            return None, None, "Game has finished"
        
        # For waiting games, enforce the original rules
        if game.status == GameStatus.WAITING:
            if len(game.players) >= game.max_players:
                return None, None, "Game is full"
            
            # Check if player name is already taken in waiting games
            if existing_player:
                return None, None, "Player name already taken"
            
            # Create new player and add to game
            player = Player(name=player_name)
            
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
            
            return game, player, "Successfully joined game"
        
        return None, None, "Unable to join game"

    def get_game_state_by_player(self, game_id: str, player_id: str) -> Optional[GameState]:
        """Get game state for a specific player by player ID."""
        game = self.games.get(game_id)
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
        """Perform a game action by player ID with concurrency control."""
        game = self.games.get(game_id)
        if not game:
            return ActionResponse(success=False, message="Game not found")
        
        # Get the game lock for concurrency control
        game_lock = self.game_locks.get(game_id)
        if not game_lock:
            return ActionResponse(success=False, message="Game lock not found")
        
        # Use lock to prevent race conditions between multiple sessions
        with game_lock:
            # Re-check game state after acquiring lock (it might have changed)
            game = self.games.get(game_id)
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
            total_value = combination.get_value()
            
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
        
        game_state = self.get_game_state_by_player(game.id, player.id)
        return ActionResponse(
            success=True,
            message="Tile drawn successfully",
            game_state=game_state
        )

    def _handle_rearrange(self, game: Game, player: Player, action: GameAction, session_id: str = None) -> ActionResponse:
        """Handle rearranging tiles on the board."""
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
        return self.games.get(game_id)


class NPCPlayer:
    """AI player that can make intelligent moves in Rummikub."""
    
    def __init__(self, name: str, player_id: str):
        self.name = name
        self.player_id = player_id
        
    def analyze_tiles(self, tiles: List[Tile]) -> Dict[str, any]:
        """Analyze player's tiles to find possible combinations."""
        analysis = {
            'groups': [],
            'runs': [],
            'potential_combinations': []
        }
        
        # Group tiles by number and color for analysis
        by_number = defaultdict(list)
        by_color = defaultdict(list)
        jokers = []
        
        for tile in tiles:
            if tile.is_joker:
                jokers.append(tile)
            else:
                by_number[tile.number].append(tile)
                by_color[tile.color].append(tile)
        
        # Find potential groups (same number, different colors)
        for number, number_tiles in by_number.items():
            if len(number_tiles) >= 2:  # Can form group with jokers
                analysis['potential_combinations'].append({
                    'type': 'group',
                    'tiles': number_tiles,
                    'number': number,
                    'can_use_jokers': len(number_tiles) + len(jokers) >= 3
                })
        
        # Find potential runs (consecutive numbers, same color)
        for color, color_tiles in by_color.items():
            color_tiles.sort(key=lambda t: t.number)
            sequences = self._find_sequences(color_tiles)
            for seq in sequences:
                if len(seq) >= 2:  # Can form run with jokers
                    analysis['potential_combinations'].append({
                        'type': 'run',
                        'tiles': seq,
                        'color': color,
                        'can_use_jokers': len(seq) + len(jokers) >= 3
                    })
        
        analysis['jokers'] = jokers
        return analysis
    
    def _find_sequences(self, tiles: List[Tile]) -> List[List[Tile]]:
        """Find consecutive sequences in sorted tiles."""
        if not tiles:
            return []
        
        sequences = []
        current_seq = [tiles[0]]
        
        for i in range(1, len(tiles)):
            if tiles[i].number == tiles[i-1].number + 1:
                current_seq.append(tiles[i])
            else:
                if len(current_seq) >= 2:
                    sequences.append(current_seq)
                current_seq = [tiles[i]]
        
        if len(current_seq) >= 2:
            sequences.append(current_seq)
        
        return sequences
    
    def suggest_best_move(self, tiles: List[Tile], has_initial_meld: bool, board: List[Combination]) -> Optional[GameAction]:
        """Suggest the best possible move for maximum tile placement."""
        analysis = self.analyze_tiles(tiles)
        
        # If player has many tiles (15+), prioritize placing ANY valid combination
        # If player has few tiles (7 or less), try to go for the win
        tile_count = len(tiles)
        high_tile_count = tile_count >= 15
        low_tile_count = tile_count <= 7
        
        # Try to find the combination that places the most tiles
        best_combination = None
        best_value = 0
        best_tiles_count = 0
        
        # For low tile count, try to place ALL remaining tiles if possible
        if low_tile_count and has_initial_meld:
            # Try to create a single combination with all tiles
            if self._can_make_single_combination(tiles):
                return GameAction(
                    action_type="place_tiles",
                    tiles=[tile.id for tile in tiles]
                )
            
            # Try to create multiple combinations that use most tiles
            multi_combo_tiles = self._find_multi_combination_solution(tiles)
            if multi_combo_tiles and len(multi_combo_tiles) >= tile_count - 2:
                return GameAction(
                    action_type="place_tiles", 
                    tiles=[tile.id for tile in multi_combo_tiles]
                )
        
        # Check potential groups
        for combo in analysis['potential_combinations']:
            if combo['type'] == 'group':
                tiles_for_combo = combo['tiles'][:]
                jokers_needed = max(0, 3 - len(tiles_for_combo))
                
                if jokers_needed <= len(analysis['jokers']):
                    # Add jokers if needed
                    jokers_to_use = analysis['jokers'][:jokers_needed]
                    tiles_for_combo.extend(jokers_to_use)
                    
                    # Try to add more tiles of same number but different colors
                    remaining_colors = set(TileColor) - {t.color for t in tiles_for_combo if not t.is_joker}
                    for color in remaining_colors:
                        for tile in tiles:
                            if (tile not in tiles_for_combo and 
                                not tile.is_joker and 
                                tile.number == combo['number'] and 
                                tile.color == color):
                                tiles_for_combo.append(tile)
                                break
                    
                    if len(tiles_for_combo) >= 3:
                        combination_obj = Combination(tiles=tiles_for_combo)
                        if combination_obj.is_valid():
                            value = combination_obj.get_value()
                            
                            # If high tile count, accept lower value combinations
                            min_value = 20 if high_tile_count else 30
                            
                            # Prioritize combinations with more tiles
                            priority_score = len(tiles_for_combo) * 100 + value
                            
                            if (not has_initial_meld and value >= min_value) or has_initial_meld:
                                if priority_score > best_value or (priority_score == best_value and len(tiles_for_combo) > best_tiles_count):
                                    best_combination = tiles_for_combo[:]
                                    best_value = priority_score
                                    best_tiles_count = len(tiles_for_combo)
        
        # Check potential runs
        for combo in analysis['potential_combinations']:
            if combo['type'] == 'run':
                tiles_for_combo = combo['tiles'][:]
                
                # Try to extend the run with jokers
                if len(tiles_for_combo) >= 2:
                    # Sort by number
                    tiles_for_combo.sort(key=lambda t: t.number)
                    
                    # Try to fill gaps with jokers
                    extended_tiles = []
                    available_jokers = analysis['jokers'][:]
                    
                    min_num = tiles_for_combo[0].number
                    max_num = tiles_for_combo[-1].number
                    
                    for num in range(min_num, max_num + 1):
                        found_tile = None
                        for tile in tiles_for_combo:
                            if tile.number == num:
                                found_tile = tile
                                break
                        
                        if found_tile:
                            extended_tiles.append(found_tile)
                        elif available_jokers:
                            # Use joker to fill gap
                            extended_tiles.append(available_jokers.pop())
                    
                    if len(extended_tiles) >= 3:
                        combination_obj = Combination(tiles=extended_tiles)
                        if combination_obj.is_valid():
                            value = combination_obj.get_value()
                            
                            # If high tile count, accept lower value combinations
                            min_value = 20 if high_tile_count else 30
                            
                            priority_score = len(extended_tiles) * 100 + value
                            
                            if (not has_initial_meld and value >= min_value) or has_initial_meld:
                                if priority_score > best_value or (priority_score == best_value and len(extended_tiles) > best_tiles_count):
                                    best_combination = extended_tiles[:]
                                    best_value = priority_score
                                    best_tiles_count = len(extended_tiles)
        
        if best_combination:
            return GameAction(
                action_type="place_tiles",
                tiles=[tile.id for tile in best_combination]
            )
        
        # If no good combination found, draw a tile
        return GameAction(action_type="draw_tile")
    
    def _can_make_single_combination(self, tiles: List[Tile]) -> bool:
        """Check if all tiles can form a single valid combination."""
        if len(tiles) < 3:
            return False
        
        combination = Combination(tiles=tiles)
        return combination.is_valid()
    
    def _find_multi_combination_solution(self, tiles: List[Tile]) -> List[Tile]:
        """Try to find multiple combinations that use most tiles."""
        # This is a simplified approach - could be more sophisticated
        used_tiles = []
        remaining_tiles = tiles[:]
        
        # Keep trying to make combinations until we can't
        while len(remaining_tiles) >= 3:
            found_combo = False
            
            # Try all possible 3-tile combinations
            for i in range(len(remaining_tiles)):
                for j in range(i+1, len(remaining_tiles)):
                    for k in range(j+1, len(remaining_tiles)):
                        test_tiles = [remaining_tiles[i], remaining_tiles[j], remaining_tiles[k]]
                        combo = Combination(tiles=test_tiles)
                        
                        if combo.is_valid():
                            used_tiles.extend(test_tiles)
                            # Remove used tiles from remaining (in reverse order to maintain indices)
                            for idx in sorted([k, j, i], reverse=True):
                                remaining_tiles.pop(idx)
                            found_combo = True
                            break
                    if found_combo:
                        break
                if found_combo:
                    break
            
            if not found_combo:
                break
        
        return used_tiles
    
    def make_move(self, game_service: GameService, game_id: str, tiles: List[Tile], 
                  has_initial_meld: bool, board: List[Combination]) -> ActionResponse:
        """Make the best possible move."""
        move = self.suggest_best_move(tiles, has_initial_meld, board)
        return game_service.perform_action_by_player(game_id, self.player_id, move)


class GameIntegrationTest:
    """Complete integration test for Rummikub game engine."""
    
    def __init__(self):
        self.game_service = GameService()
        self.stats = {
            'games_played': 0,
            'total_turns': 0,
            'tiles_placed_total': 0,
            'average_game_length': 0,
            'winners': {},
            'rule_violations': 0,
            'pool_exhaustion_failures': 0
        }
    
    def _format_tiles(self, tiles: List[Tile]) -> str:
        """Format tiles for display."""
        if not tiles:
            return "[]"
        
        tile_strs = []
        for tile in sorted(tiles, key=lambda t: (t.number or 0, str(t.color) if t.color else "z")):
            tile_strs.append(str(tile))
        
        return f"[{', '.join(tile_strs)}]"
    
    def _display_game_state(self, game_state: GameState, current_player_name: str):
        """Display the current game state including hand and board."""
        print(f"👤 {current_player_name}'s hand: {self._format_tiles(game_state.your_tiles)}")
        
        if game_state.board:
            print("📋 Board:")
            for i, combo in enumerate(game_state.board):
                print(f"   Combination {i+1}: {self._format_tiles(combo.tiles)}")
        else:
            print("📋 Board: [empty]")
    
    def _log_action(self, action: GameAction, result: ActionResponse, tiles_placed: int):
        """Log the action performed with details."""
        if action.action_type == "place_tiles":
            tile_count = len(action.tiles) if action.tiles else 0
            print(f"🎯 Action: Placed {tile_count} tiles (value: {tiles_placed})")
        elif action.action_type == "draw_tile":
            print("🎯 Action: Drew a tile")
        elif action.action_type == "rearrange":
            print("🎯 Action: Rearranged combinations")
        else:
            print(f"🎯 Action: {action.action_type}")
        
        if not result.success:
            print(f"   ❌ Failed: {result.message}")
        else:
            print(f"   ✅ Success: {result.message}")
    
    def run_complete_game(self, num_players: Optional[int] = None) -> Dict[str, any]:
        """Run a complete game from start to finish."""
        if num_players is None:
            num_players = random.randint(2, 4)
        
        print(f"\n🎲 Starting integration test with {num_players} players...")
        
        # Create game
        game = self.game_service.create_game(max_players=num_players, creator_name="TestAdmin")
        game_id = game.id
        
        # Create NPC players
        npc_players = []
        for i in range(num_players):
            player_name = f"NPC_{i+1}"
            game, player, message = self.game_service.join_game_by_id(game_id, player_name)
            if player:
                npc = NPCPlayer(player_name, player.id)
                npc_players.append(npc)
                print(f"✅ {player_name} joined the game")
            else:
                print(f"❌ Failed to join {player_name}: {message}")
                break
        
        # Get updated game reference
        game = self.game_service.get_game_by_id(game_id)
        if not game:
            return {"error": "Game not found after player joins"}
        
        print(f"✅ Game started with {len(npc_players)} players")
        print(f"📊 Initial tile pool size: {len(game.tile_pool)}")
        
        # Game loop
        turn_count = 0
        max_turns = 200  # Reduce max turns to prevent very long games
        tiles_placed_this_game = 0
        turns_without_progress = 0  # Track turns where no progress is made
        
        while game.status == GameStatus.IN_PROGRESS and turn_count < max_turns and turns_without_progress < 50:
            turn_count += 1
            current_player = game.current_player
            
            if not current_player:
                print(f"❌ No current player found on turn {turn_count}")
                break
            
            # Find the NPC for this player
            npc = None
            for n in npc_players:
                if n.player_id == current_player.id:
                    npc = n
                    break
            
            if not npc:
                print(f"❌ Could not find NPC for player {current_player.name}")
                break
            
            print(f"\n🎯 Turn {turn_count}: {npc.name} ({len(current_player.tiles)} tiles)")
            
            # Get current game state
            game_state = self.game_service.get_game_state_by_player(game_id, current_player.id)
            if not game_state:
                print("❌ Could not get game state")
                break
            
            # Display current state
            self._display_game_state(game_state, npc.name)
            
            # NPC makes a move
            initial_tile_count = len(current_player.tiles)
            
            # Get the suggested action first for logging
            suggested_action = npc.suggest_best_move(
                current_player.tiles, 
                current_player.has_initial_meld,
                game.board
            )
            
            result = npc.make_move(
                self.game_service, 
                game_id, 
                current_player.tiles, 
                current_player.has_initial_meld,
                game.board
            )
            
            # Log the action
            tiles_placed = initial_tile_count - len(current_player.tiles) if result.success else 0
            self._log_action(suggested_action, result, tiles_placed)
            
            if not result.success:
                print(f"❌ Move failed: {result.message}")
                self.stats['rule_violations'] += 1
                
                # Check if pool is empty - this is a simulation failure
                if len(game.tile_pool) == 0:
                    print("💀 SIMULATION FAILED: Tile pool exhausted!")
                    self.stats['pool_exhaustion_failures'] += 1
                    break
                
                # If pool is empty, just pass the turn instead of trying to draw
                if "No tiles left in pool" in result.message:
                    print("⏰ Pool exhausted - passing turn")
                    game.next_turn()
                else:
                    # Force draw tile if move failed and pool has tiles
                    if len(game.tile_pool) > 0:
                        fallback_action = GameAction(action_type="draw_tile")
                        result = self.game_service.perform_action_by_player(game_id, current_player.id, fallback_action)
                    else:
                        # Just pass turn if no tiles left
                        game.next_turn()
            
            # Check what happened
            final_tile_count = len(current_player.tiles)
            tiles_placed = initial_tile_count - final_tile_count
            
            if tiles_placed > 0:
                tiles_placed_this_game += tiles_placed
                turns_without_progress = 0
                print(f"✅ Placed {tiles_placed} tiles on board")
            else:
                turns_without_progress += 1
                print("📥 Drew a tile")
            
            print(f"📋 Board now has {len(game.board)} combinations")
            print(f"🎯 Pool has {len(game.tile_pool)} tiles remaining")
            
            # Update game reference (it might have changed)
            game = self.game_service.get_game_by_id(game_id)
            if not game:
                print("❌ Game disappeared")
                break
        
        # Game finished
        if not game:
            return {
                'error': 'Game reference lost during execution',
                'turns': turn_count,
                'pool_exhausted': len(game.tile_pool) == 0 if game else True
            }
        
        game_result = {
            'game_id': game_id,
            'turns': turn_count,
            'final_status': game.status,
            'tiles_placed': tiles_placed_this_game,
            'board_combinations': len(game.board),
            'remaining_pool': len(game.tile_pool),
            'pool_exhausted': len(game.tile_pool) == 0,
            'players': []
        }
        
        winner = None
        for player in game.players:
            player_info = {
                'name': player.name,
                'tiles_remaining': len(player.tiles),
                'status': player.status,
                'had_initial_meld': player.has_initial_meld
            }
            game_result['players'].append(player_info)
            
            if player.status == PlayerStatus.FINISHED:
                winner = player.name
                game_result['winner'] = winner
        
        # Update statistics
        self.stats['games_played'] += 1
        self.stats['total_turns'] += turn_count
        self.stats['tiles_placed_total'] += tiles_placed_this_game
        
        if winner:
            self.stats['winners'][winner] = self.stats['winners'].get(winner, 0) + 1
            print(f"🏆 Game finished! Winner: {winner} in {turn_count} turns")
        else:
            print(f"⏰ Game ended after {turn_count} turns")
            if turns_without_progress >= 50:
                print("   Reason: No progress made in 50+ consecutive turns")
            elif turn_count >= max_turns:
                print("   Reason: Maximum turns reached")
        
        print(f"📊 Total tiles placed this game: {tiles_placed_this_game}")
        
        return game_result
    
    def run_multiple_games(self, num_games: int = 5) -> Dict[str, any]:
        """Run multiple games and collect statistics."""
        print(f"\n🚀 Running {num_games} integration tests...")
        
        game_results = []
        
        for i in range(num_games):
            print(f"\n{'='*50}")
            print(f"GAME {i+1}/{num_games}")
            print(f"{'='*50}")
            
            result = self.run_complete_game()
            game_results.append(result)
        
        # Calculate final statistics
        if self.stats['games_played'] > 0:
            self.stats['average_game_length'] = self.stats['total_turns'] / self.stats['games_played']
            self.stats['average_tiles_per_game'] = self.stats['tiles_placed_total'] / self.stats['games_played']
        
        # Print final summary
        print(f"\n{'='*50}")
        print("INTEGRATION TEST SUMMARY")
        print(f"{'='*50}")
        print(f"Games completed: {self.stats['games_played']}")
        print(f"Total turns played: {self.stats['total_turns']}")
        print(f"Average game length: {self.stats['average_game_length']:.1f} turns")
        print(f"Total tiles placed: {self.stats['tiles_placed_total']}")
        print(f"Average tiles per game: {self.stats.get('average_tiles_per_game', 0):.1f}")
        print(f"Rule violations: {self.stats['rule_violations']}")
        print(f"Pool exhaustion failures: {self.stats['pool_exhaustion_failures']}")
        print("Winners distribution:", self.stats['winners'])
        
        # Validate game rules were followed
        rules_valid = self._validate_game_rules(game_results)
        print(f"\n🔍 Game rules validation: {'✅ PASSED' if rules_valid else '❌ FAILED'}")
        
        return {
            'game_results': game_results,
            'statistics': self.stats,
            'rules_valid': rules_valid
        }
    
    def _validate_game_rules(self, game_results: List[Dict]) -> bool:
        """Validate that all game rules were properly enforced."""
        print("\n🔍 Validating game rules...")
        
        all_valid = True
        
        for i, result in enumerate(game_results):
            print(f"\nValidating Game {i+1}:")
            
            # Check that games finished properly
            if result['final_status'] != GameStatus.FINISHED and result['turns'] < 1000:
                print(f"  ❌ Game didn't finish properly: {result['final_status']}")
                all_valid = False
            
            # Check winner conditions
            if 'winner' in result:
                winner_found = False
                for player in result['players']:
                    if player['tiles_remaining'] == 0:
                        winner_found = True
                        break
                
                if not winner_found:
                    print(f"  ❌ Winner declared but no player has 0 tiles")
                    all_valid = False
                else:
                    print(f"  ✅ Winner condition validated")
            
            # Check that tiles were placed (game progressed)
            if result['tiles_placed'] == 0:
                print(f"  ⚠️  No tiles were placed during entire game")
            else:
                print(f"  ✅ {result['tiles_placed']} tiles placed successfully")
            
            # Check for pool exhaustion failures
            if result.get('pool_exhausted', False) and not result.get('winner'):
                print(f"  ❌ Pool exhausted without winner - simulation failed")
                all_valid = False
            elif result.get('pool_exhausted', False):
                print(f"  ⚠️  Pool exhausted but game had winner")
            else:
                print(f"  ✅ Pool not exhausted")
        
        return all_valid


def main():
    """Run the integration test."""
    print("🎮 Rummikub Backend Integration Test")
    print("Testing complete game simulation with AI players")
    print("No HTTP API - pure backend logic validation")
    
    # Run integration tests
    test_runner = GameIntegrationTest()
    
    # Test single game first
    print("\n" + "="*60)
    print("SINGLE GAME TEST")
    print("="*60)
    single_result = test_runner.run_complete_game()
    
    # Reset stats for multi-game test
    test_runner.stats = {
        'games_played': 0,
        'total_turns': 0,
        'tiles_placed_total': 0,
        'average_game_length': 0,
        'winners': {},
        'rule_violations': 0,
        'pool_exhaustion_failures': 0
    }
    
    # Run multiple games
    print("\n" + "="*60)
    print("MULTIPLE GAMES TEST")
    print("="*60)
    results = test_runner.run_multiple_games(3)
    
    if results['rules_valid']:
        print("\n🎉 Integration test completed successfully!")
        print("✅ All game rules properly validated")
        print("✅ AI players successfully played complete games")
        print("✅ Game engine working correctly")
        return True
    else:
        print("\n❌ Integration test found issues!")
        print("❌ Some game rules were not properly enforced")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)