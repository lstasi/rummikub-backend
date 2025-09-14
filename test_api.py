#!/usr/bin/env python3
"""
Simple test script to verify Rummikub API functionality.
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


def test_api():
    """Test the API endpoints."""
    print("🎲 Testing Rummikub API...")
    
    # Test root endpoint
    print("\n1. Testing root endpoint...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test game creation (with auth and creator name)
    print("\n2. Testing game creation...")
    auth_headers = create_auth_header()
    game_data = {"max_players": 4, "name": "TestCreator"}
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
    
    # Test joining game
    print("\n3. Testing game join...")
    join_data = {
        "game_id": game_id,
        "player_name": "TestPlayer1"
    }
    response = requests.post(f"{BASE_URL}/game/{game_id}/join", json=join_data)
    print(f"Status: {response.status_code}")
    join_info = response.json()
    print(f"Response keys: {join_info.keys()}")
    
    if response.status_code != 200:
        print("❌ Failed to join game")
        return
    
    access_token = join_info["access_token"]
    print(f"✅ Player joined with token")
    
    # Test game state
    print("\n4. Testing game state...")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/game/{game_id}", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        game_state = response.json()
        print(f"Game status: {game_state['status']}")
        print(f"Your tiles count: {len(game_state['your_tiles'])}")
        print(f"Board combinations: {len(game_state['board'])}")
        print(f"Can play: {game_state['can_play']}")
        print("✅ Game state retrieved successfully")
    else:
        print(f"❌ Failed to get game state: {response.json()}")
    
    # Test game info (no auth required)
    print("\n5. Testing game info...")
    response = requests.get(f"{BASE_URL}/game/{game_id}/info")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        info = response.json()
        print(f"Player count: {info['player_count']}/{info['max_players']}")
        print("✅ Game info retrieved successfully")
    
    print("\n🎉 All tests completed!")


if __name__ == "__main__":
    try:
        test_api()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Make sure the server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")