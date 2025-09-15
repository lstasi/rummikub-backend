# Multi-Screen Access Feature

This document describes the multi-screen access functionality implemented for the Rummikub Backend API.

## Overview

The multi-screen access feature allows players to connect to the same game from multiple devices or browser windows simultaneously. Each connection receives a unique authentication token while maintaining access to the same player's game state.

## Key Features

### 1. Multiple Session Support
- Players can join the same game multiple times using the same player name
- Each join creates a new session with a unique JWT token
- Sessions are independent but access the same player data

### 2. Concurrent Action Protection
- When multiple sessions attempt actions simultaneously, only the first action is processed
- Subsequent concurrent actions receive an error response
- Uses threading locks to prevent race conditions

### 3. Seamless Re-joining
- Players can re-join games that are already in progress
- Works for games where the player is already a participant
- Does not allow joining finished games

## Technical Implementation

### Authentication Changes
- JWT tokens now include a unique `session_id` field
- Each call to `/game/{game_id}/join` generates a new token
- Tokens remain valid for 24 hours as before

### Game Service Enhancements
- Added `threading.Lock` for each game to prevent race conditions
- Modified `join_game_by_id()` to allow re-joining in-progress games
- Added session tracking and concurrency control

### API Behavior
- **Waiting Games**: Players cannot join with duplicate names (original behavior)
- **In-Progress Games**: Players can re-join with existing names (new multi-screen behavior)
- **Finished Games**: No new joins allowed (original behavior)

## Usage Examples

### Basic Multi-Screen Access
```bash
# Player joins from first device
curl -X POST "http://localhost:8090/game/{game_id}/join" \
  -H "Content-Type: application/json" \
  -d '{"player_name": "Alice"}'

# Same player joins from second device (after game starts)
curl -X POST "http://localhost:8090/game/{game_id}/join" \
  -H "Content-Type: application/json" \
  -d '{"player_name": "Alice"}'
```

### Using Multiple Sessions
```bash
# Both tokens can access game state
curl "http://localhost:8090/game/{game_id}" \
  -H "Authorization: Bearer {token1}"

curl "http://localhost:8090/game/{game_id}" \
  -H "Authorization: Bearer {token2}"

# But only one action succeeds when attempted concurrently
curl -X POST "http://localhost:8090/game/{game_id}/action" \
  -H "Authorization: Bearer {token1}" \
  -H "Content-Type: application/json" \
  -d '{"action_type": "draw_tile"}'
```

## Testing

The feature includes comprehensive test suites:

### Test Files
- `test_multiscreen.py` - Core multi-screen functionality tests
- `test_edge_cases.py` - Edge cases and error conditions
- `demo_multiscreen.py` - Interactive demonstration script

### Test Coverage
- ✅ Re-joining games in progress
- ✅ Unique token generation per session
- ✅ Concurrent action handling
- ✅ Game state synchronization across sessions
- ✅ Edge cases (waiting games, finished games, non-existent games)
- ✅ Backward compatibility with existing functionality

## Error Handling

### Scenarios that Fail (Expected Behavior)
- Joining waiting games with duplicate names
- Joining finished games
- Joining non-existent games
- New players joining in-progress games

### Scenarios that Succeed (New Functionality)
- Re-joining in-progress games with existing player name
- Multiple sessions accessing game state
- First concurrent action processed, others rejected

## Performance Considerations

- Thread-safe implementation using `threading.Lock`
- Minimal overhead - locks are per-game, not global
- Session tracking adds negligible memory overhead
- No changes to existing API response times

## Backward Compatibility

The implementation maintains full backward compatibility:
- Existing clients continue to work unchanged
- All original API behaviors preserved
- No breaking changes to request/response formats
- New functionality is additive only

## Configuration

No additional configuration required. The feature works with existing:
- JWT secret and algorithm
- Database/storage (in-memory)
- Authentication mechanisms
- API endpoints

## Limitations

- Sessions are tied to JWT token expiration (24 hours)
- No persistent session storage (lost on server restart)
- Concurrency protection is first-come-first-served
- No real-time synchronization (clients must poll for updates)

## Future Enhancements

Potential improvements for future versions:
- WebSocket support for real-time updates
- Persistent session storage
- Session management UI
- Advanced concurrency controls (queuing, prioritization)
- Session expiration notifications