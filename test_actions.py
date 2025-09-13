#!/usr/bin/env python3
"""
Extended test script to verify Rummikub API functionality including game actions.
"""
import requests
import json
import base64
import time

BASE_URL = "http://localhost:8000"
ADMIN_USER = "admin"
ADMIN_PASS = "rummikub2024"


def create_auth_header():
    """Create basic auth header."""
    credentials = f"{ADMIN_USER}:{ADMIN_PASS}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded_credentials}"}


def test_game_actions():
    """Test game actions including placing tiles and drawing tiles."""
    print("🎲 Testing Rummikub Game Actions...")
    
    # Create game
    auth_headers = create_auth_header()
    game_data = {"max_players": 2}
    response = requests.post(f"{BASE_URL}/game", json=game_data, headers=auth_headers)
    game_info = response.json()
    game_id = game_info["game_id"]
    invite_code = game_info["invite_code"]
    print(f"✅ Created game: {invite_code}")
    
    # Join game with first player
    join_data = {"invite_code": invite_code, "player_name": "Player1"}
    response = requests.post(f"{BASE_URL}/game/{game_id}/join", json=join_data)
    player1_info = response.json()
    session1 = player1_info["session_id"]
    print(f"✅ Player1 joined")
    
    # Join game with second player  
    join_data = {"invite_code": invite_code, "player_name": "Player2"}
    response = requests.post(f"{BASE_URL}/game/{game_id}/join", json=join_data)
    player2_info = response.json()
    session2 = player2_info["session_id"]
    print(f"✅ Player2 joined - Game should now be in progress")
    
    # Get game state for player 1
    response = requests.get(f"{BASE_URL}/game/{game_id}?session_id={session1}")
    game_state = response.json()
    print(f"Game status: {game_state['status']}")
    print(f"Current player: {game_state['current_player']}")
    print(f"Can Player1 play: {game_state['can_play']}")
    print(f"Player1 has {len(game_state['your_tiles'])} tiles")
    
    # Try to draw a tile (player 1's turn)
    if game_state['can_play']:
        print("\n🎯 Testing draw tile action...")
        action_data = {"action_type": "draw_tile"}
        response = requests.post(
            f"{BASE_URL}/game/{game_id}/action?session_id={session1}",
            json=action_data
        )
        print(f"Draw tile status: {response.status_code}")
        if response.status_code == 200:
            action_result = response.json()
            print(f"✅ {action_result['message']}")
            print(f"Now have {len(action_result['game_state']['your_tiles'])} tiles")
        else:
            print(f"❌ Draw failed: {response.json()}")
    
    # Get updated game state
    response = requests.get(f"{BASE_URL}/game/{game_id}?session_id={session2}")
    game_state = response.json()
    print(f"\nAfter Player1's turn:")
    print(f"Current player: {game_state['current_player']}")
    print(f"Can Player2 play: {game_state['can_play']}")
    
    # Try an invalid action (wrong player's turn)
    print("\n🚫 Testing invalid action (wrong turn)...")
    action_data = {"action_type": "draw_tile"}
    response = requests.post(
        f"{BASE_URL}/game/{game_id}/action?session_id={session1}",
        json=action_data
    )
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"✅ Correctly rejected: {response.json()['detail']}")
    
    print("\n🎉 Game action tests completed!")


if __name__ == "__main__":
    try:
        test_game_actions()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Make sure the server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")