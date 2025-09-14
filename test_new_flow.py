#!/usr/bin/env python3
"""
Test script to verify the new Bearer token authentication flow.
"""
import requests
import json
import base64

BASE_URL = "http://localhost:8000"
ADMIN_USER = "admin"
ADMIN_PASS = "rummikub2024"


def create_auth_header():
    """Create basic auth header for admin."""
    credentials = f"{ADMIN_USER}:{ADMIN_PASS}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded_credentials}"}


def test_new_auth_flow():
    """Test the new Bearer token authentication flow."""
    print("🎲 Testing New Rummikub Authentication Flow...")
    
    # Test 1: Create game with creator name
    print("\n1. Testing game creation with creator name...")
    auth_headers = create_auth_header()
    game_data = {
        "max_players": 2,
        "name": "GameMaster"
    }
    response = requests.post(
        f"{BASE_URL}/game", 
        json=game_data, 
        headers=auth_headers
    )
    print(f"Status: {response.status_code}")
    game_info = response.json()
    print(f"Response: {game_info}")
    
    if response.status_code != 200:
        print("❌ Failed to create game")
        return
    
    game_id = game_info["game_id"]
    print(f"✅ Game created with ID: {game_id}")
    
    # Test 2: Join game with game_id and player name
    print("\n2. Testing game join with game_id...")
    join_data = {
        "game_id": game_id,
        "player_name": "Player1"
    }
    response = requests.post(f"{BASE_URL}/game/{game_id}/join", json=join_data)
    print(f"Status: {response.status_code}")
    join_info = response.json()
    print(f"Response keys: {join_info.keys()}")
    
    if response.status_code != 200:
        print(f"❌ Failed to join game: {response.json()}")
        return
    
    access_token = join_info["access_token"]
    print(f"✅ Player joined with token: {access_token[:20]}...")
    
    # Test 3: Get game state with Bearer token
    print("\n3. Testing game state with Bearer token...")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/game/{game_id}", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        game_state = response.json()
        print(f"Game status: {game_state['status']}")
        print(f"Your tiles count: {len(game_state['your_tiles'])}")
        print(f"Can play: {game_state['can_play']}")
        print("✅ Game state retrieved with Bearer token")
    else:
        print(f"❌ Failed to get game state: {response.json()}")
        return
    
    # Test 4: Join second player to start the game
    print("\n4. Testing second player join...")
    join_data2 = {
        "game_id": game_id,
        "player_name": "Player2"
    }
    response = requests.post(f"{BASE_URL}/game/{game_id}/join", json=join_data2)
    if response.status_code == 200:
        player2_info = response.json()
        access_token2 = player2_info["access_token"]
        print(f"✅ Player2 joined - Game should now be in progress")
    else:
        print(f"❌ Failed to join second player: {response.json()}")
        return
    
    # Test 5: Perform action with Bearer token
    print("\n5. Testing action with Bearer token...")
    headers = {"Authorization": f"Bearer {access_token}"}
    action_data = {"action_type": "draw_tile"}
    response = requests.post(
        f"{BASE_URL}/game/{game_id}/action",
        json=action_data,
        headers=headers
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        action_result = response.json()
        print(f"✅ {action_result['message']}")
        print(f"Now have {len(action_result['game_state']['your_tiles'])} tiles")
    else:
        print(f"❌ Action failed: {response.json()}")
    
    # Test 6: Test invalid token
    print("\n6. Testing invalid token...")
    headers = {"Authorization": "Bearer invalid_token"}
    response = requests.get(f"{BASE_URL}/game/{game_id}", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 401:
        print("✅ Invalid token correctly rejected")
    else:
        print(f"❌ Invalid token should be rejected: {response.json()}")
    
    print("\n🎉 New authentication flow tests completed!")


if __name__ == "__main__":
    try:
        test_new_auth_flow()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Make sure the server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")